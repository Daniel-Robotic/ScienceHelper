import json
import pathlib
import re
from typing import Any

import PyPDF2

from science_helper.utils.setting import RE_DATE, RE_ISSN_RAW, RE_ROW_START, RE_SPEC_CODE


class PDFParser:
    """Parses a structured PDF file containing journal metadata such as title, ISSN, and specialties.

    This class provides functionality for reading a PDF file, extracting textual content,
    parsing it into sections, and extracting structured metadata from each section.
    
    Attributes:
        path (Path): Path to the PDF file to be parsed.
    """  # noqa: E501

    def __init__(self, path: str | pathlib.Path):
        """Initialize the parser with the path to a PDF file.

        Args:
            path (str | Path): Path to the PDF file.
        """
        self.path = pathlib.Path(path)

    def _read_pdf_text(self) -> str:
        """Read and extract all text content from the PDF file.

        Returns:
            str: Combined text from all pages of the PDF with normalized line endings.
        """
        reader = PyPDF2.PdfReader(self.path)
        return "\n".join(page.extract_text() or "" for page in reader.pages).replace("\r", "")

    def _split_sections(self, raw: str) -> list[str]:
        """Split the raw text into sections using a regular expression pattern.

        Each section is assumed to start with a recognizable numeric identifier
        based on the `RE_ROW_START` pattern.

        Args:
            raw (str): Raw text extracted from the PDF.

        Returns:
            list[str]: List of text segments corresponding to logical journal entries.
        """
        idx = [m.start() for m in RE_ROW_START.finditer(raw)] + [len(raw)]
        return [raw[idx[i] : idx[i + 1]] for i in range(len(idx) - 1)]

    def _normalize_issn(self, raw: str) -> str:
        """Normalize ISSN text to a consistent format (uppercase, hyphenated).

        Args:
            raw (str): Raw ISSN string.

        Returns:
            str: Normalized ISSN string.
        """
        raw = raw.replace("Х", "X").replace("х", "x")
        raw = re.sub(r"[\-‑–—−]", "-", raw)
        raw = re.sub(r"\s*-\s*", "-", raw)
        return raw.upper()

    def _split_specialties(self, tail: str) -> list[str]:
        """Split a string containing specialty codes into a clean list of values.

        Args:
            tail (str): Text segment that may contain multiple specialty codes.

        Returns:
            list[str]: List of extracted and cleaned specialty codes.
        """
        specs = []
        matches = list(RE_SPEC_CODE.finditer(tail))
        if not matches:
            raw_parts = [s.strip() for s in tail.split(",") if s.strip()]
        else:
            raw_parts = []
            for i, m in enumerate(matches):
                start = m.start()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(tail)
                raw_parts.append(tail[start:end].strip().lstrip(",; )"))
        for seg in raw_parts:
            cleaned_seg = seg.replace(",", " ")
            cleaned_seg = re.sub(r"\s{2,}", " ", cleaned_seg)
            if cleaned_seg:
                specs.append(cleaned_seg)
        return specs

    def _parse_section(self, sec: str) -> dict[str, Any] | None:
        """Parse a single section of text into structured metadata.

        Args:
            sec (str): Text section representing a single journal entry.

        Returns:
            dict[str, Any] | None: Dictionary with keys:
                - "N": Entry number
                - "title": Journal title
                - "issn": Normalized ISSN (if present)
                - "specialties": List of specialty codes (if present)
            Returns None if the section is not properly formatted.
        """
        clean = sec.replace("\r", "").replace("\n", " ")
        m_num = RE_ROW_START.match(clean)
        if not m_num:
            return None
        n = int(m_num.group(1))
        body = clean[m_num.end() :].strip()

        issn_iter = list(RE_ISSN_RAW.finditer(body))
        if issn_iter:
            last = issn_iter[-1]
            issn = self._normalize_issn(last.group(0))
            before, after = body[: last.start()].strip(), body[last.end() :].strip()
        else:
            issn, before, after = "", body, ""

        specialties = []
        if after:
            tail = RE_DATE.sub("", after).strip()
            tail = RE_ISSN_RAW.sub("", tail).strip()
            specialties = self._split_specialties(tail)

        title = re.sub(r"\s{2,}", " ", before).strip()
        return {"N": n, "title": title, "issn": issn, "specialties": specialties}

    def parse(self) -> list[dict[str, Any]]:
        """Read the PDF file and parses it into a list of structured records.

        Returns:
            list[dict[str, Any]]: List of dictionaries, each representing a parsed journal entry.

        Raises:
            FileNotFoundError: If the PDF file does not exist.
        """
        if not self.path.exists():
            raise FileNotFoundError(f"Файл {self.path} не найден")
        raw = self._read_pdf_text()
        sections = self._split_sections(raw)
        rows = [r for r in (self._parse_section(s) for s in sections) if r]
        return sorted(rows, key=lambda d: d["N"])


def save_to_json(
    rows: list[dict[str, Any]], out_path: str | pathlib.Path | None = None
) -> pathlib.Path:
    """Save a list of dictionaries to a JSON file.

    If `out_path` is not provided, the file is saved as 'vak_articles.json'
    in the current working directory.

    Args:
        rows (list[dict[str, Any]]): The list of dictionaries to save.
        out_path (str | pathlib.Path | None): The path to save the JSON file to.

    Returns:
        pathlib.Path: The path to the saved JSON file.
    """
    out_path = pathlib.Path(out_path or "vak_articles.json")
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    return out_path


def load_json(in_path: str | pathlib.Path) -> list[dict[str, Any]]:
    """Load and parse a JSON file into a list of dictionaries.

    Args:
        in_path (str | pathlib.Path): Path to the JSON file.

    Returns:
        list[dict[str, Any]]: The parsed content of the JSON file.
    """
    with in_path.open("r", encoding="utf-8") as f:
        return json.load(f)
