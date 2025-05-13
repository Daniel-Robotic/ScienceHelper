import json
import re
import pathlib
from typing import List, Dict, Any
from setting import (RE_ROW_START, 
                       RE_ISSN_RAW,
                       RE_DATE,
                       RE_SPEC_CODE,
                       RE_INNER_SPACE)

import PyPDF2


def _read_pdf_text(pdf_path: pathlib.Path | str) -> str:
    reader = PyPDF2.PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages).replace("\r", "")


def _split_sections(raw: str) -> List[str]:
    idx = [m.start() for m in RE_ROW_START.finditer(raw)] + [len(raw)]
    return [raw[idx[i]:idx[i+1]] for i in range(len(idx)-1)]


def _normalize_issn(raw: str) -> str:
    raw = raw.replace("Х", "X").replace("х", "x")
    raw = re.sub(r"[\-‑–—−]", "-", raw)
    raw = re.sub(r"\s*-\s*", "-", raw)
    return raw.upper()

def _split_specialties(tail: str) -> List[str]:
    specs: List[str] = []
    matches = list(RE_SPEC_CODE.finditer(tail))
    if not matches:
        raw_parts = [s.strip() for s in tail.split(',') if s.strip()]
    else:
        raw_parts = []
        for i, m in enumerate(matches):
            start = m.start()
            end = matches[i+1].start() if i+1 < len(matches) else len(tail)
            raw_parts.append(tail[start:end].strip().lstrip(',; )'))

    for seg in raw_parts:
        seg = seg.replace(',', ' ')
        seg = re.sub(r"\s{2,}", " ", seg)
        if seg:
            specs.append(seg)
    return specs


def _parse_section(sec: str) -> Dict[str, Any] | None:
    clean = sec.replace("\r", "").replace("\n", " ")
    m_num = RE_ROW_START.match(clean)
    if not m_num:
        return None
    n = int(m_num.group(1))
    body = clean[m_num.end():].strip()

    issn_iter = list(RE_ISSN_RAW.finditer(body))
    if issn_iter:
        last = issn_iter[-1]
        issn = _normalize_issn(last.group(0))
        before, after = body[:last.start()].strip(), body[last.end():].strip()
    else:
        issn, before, after = "", body, ""

    specialties: List[str] = []
    if after:
                # вырезаем любые фрагменты вида "с 16.12.2021" но НЕ обрезаем хвост
        tail = RE_DATE.sub("", after).strip()
        tail = RE_ISSN_RAW.sub("", tail).strip()
        specialties = _split_specialties(tail)

    title = re.sub(r"\s{2,}", " ", before).strip()
    return {"N": n, "title": title, "issn": issn, "specialties": specialties}


# ---------------------------------------------------------------------------
# Фильтрация
# ---------------------------------------------------------------------------
def fizbuz(spec_line: str, targets: List[str]) -> bool:
    return any(spec_line.startswith(t) for t in targets)


def filter_rows_by_specialty(rows: List[Dict[str, Any]], targets: List[str]) -> List[Dict[str, Any]]:
    if not targets or any(t.lower() == "all" for t in targets):
        return rows  # без фильтра
    return [r for r in rows if any(fizbuz(sp, targets) for sp in r["specialties"])]


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
def parse_vak_pdf(pdf_path: str | pathlib.Path) -> List[Dict[str, Any]]:
    path = pathlib.Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"Файл {pdf_path} не найден")
    raw = _read_pdf_text(path)
    sections = _split_sections(raw)
    rows = [r for r in (_parse_section(s) for s in sections) if r]
    rows.sort(key=lambda d: d["N"])
    return rows


def save_to_json(rows: List[Dict[str, Any]], out_path: str | pathlib.Path | None = None) -> pathlib.Path:
    out_path = pathlib.Path(out_path or "vak_articles.json")
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    return out_path

def load_json(in_path: str | pathlib.Path | None = None) -> List[dict]:
    with in_path.open('r', encoding="utf-8") as f:
        data = json.loads(f.read())

    return data