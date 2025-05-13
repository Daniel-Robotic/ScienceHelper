from __future__ import annotations

from .downloader import (download_pdf_if_needed, 
						dict_from_web,
						get_nomenclature_scientific_specialties)
from .pdf_parser import (parse_vak_pdf, 
						filter_rows_by_specialty, 
						save_to_json,
						load_json)

__all__ = [
    "parse_vak_pdf",
    "save_to_json",
    "filter_rows_by_specialty",
	"download_pdf_if_needed",
	"dict_from_web",
	"bool_to_YesNo",
	"get_nomenclature_scientific_specialties",
	"load_json"
]

def bool_to_YesNo(element):
	return "Да" if element else "Нет"




