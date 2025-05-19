from __future__ import annotations

from .downloader import PDFDownloader
from .filters import filter_rows_by_specialty
from .nomenclature import NomenclatureParser
from .pdf_parser import PDFParser, load_json, save_to_json


def bool_to_yes_no(val: bool) -> str:
    return "Да" if val else "Нет"

__all__ = [
    "NomenclatureParser",
    "PDFDownloader",
    "PDFParser",
    "bool_to_YesNo",
    "filter_rows_by_specialty",
    "load_json",
    "save_to_json"
]