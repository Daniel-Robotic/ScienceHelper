import requests
import configparser

from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from utils.pdf_parser import save_to_json

def download_pdf_if_needed(url: str, 
                           output_dir: str = ".", 
                           config_path: str = "config.ini",
                           timeout: int = 60) -> Path:
    # --- Извлекаем имя файла по параметру `name=...`
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    name = params.get("name", [None])[0]
    if not name:
        raise ValueError("URL не содержит параметра ?name=...")

    filename = f"{name}.pdf"
    filepath = Path(output_dir) / filename

    # --- Пропускаем загрузку, если файл уже есть
    if filepath.exists():
        print(f"[✓] Файл уже существует: {filepath}")
    else:
        resp = requests.get(url, 
                            timeout=timeout, 
                            verify=False)
        resp.raise_for_status()
        filepath.write_bytes(resp.content)
        print(f"[↓] Скачано: {filepath}")

    config = configparser.ConfigParser()
    config.read(config_path, encoding="utf-8")
    config["DIRECTORY"]["filename"] = filename
    with open(config_path, "w", encoding="utf-8") as f:
        config.write(f)
    
    return filepath


def dict_from_web(url: str, output_dir: str = "./",  timeout: int = 60) -> dict:
    r = requests.get(url, 
                     timeout=timeout, 
                     verify=False)
    if not r.status_code == 200:
        return({})
    
    save_to_json(r.json(), output_dir)


def get_nomenclature_scientific_specialties(url: str, timeout: int = 60) -> list[dict]:
    r = requests.get(url=url, timeout=timeout, verify=False)
    
    if not r.status_code == 200:
        return({})
    

    output = []
    current_main = None
    current_sub = None
    main_index = {}

    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find("table")

    if table:
        rows = table.find_all("tr")

        for row in rows[1:]:
            cells = row.find_all("td")
            if not cells:
                continue
            
            text_cells = [cell.get_text(strip=True) for cell in cells]
            if all(not txt for txt in text_cells):
                continue

            if len(cells) == 4:
                if cells[0].has_attr("rowspan"):
                    current_main = cells[0].get_text(strip=True)
                    output.append({
                        "category_name": current_main,
                        "sub_category": []
                    })
                if cells[1].has_attr("rowspan"):
                    current_sub = cells[1].get_text(strip=True)
                    sub_entry = {
                        "subcategory_name": current_sub,
                        "values": [cells[2].get_text(strip=True)]
                    }
                    output[-1]["sub_category"].append(sub_entry)
                else:
                    output[-1]["sub_category"][-1]["values"].append(cells[2].get_text(strip=True))


            elif len(cells) == 3:
                if cells[0].has_attr("rowspan"):
                    current_sub = cells[0].get_text(strip=True)
                    sub_entry = {
                        "subcategory_name": current_sub,
                        "values": [cells[1].get_text(strip=True)]
                    }
                    output[-1]["sub_category"].append(sub_entry)
                else:
                    output[-1]["sub_category"][-1]["values"].append(cells[1].get_text(strip=True))

            elif len(cells) == 2:
                output[-1]["sub_category"][-1]["values"].append(cells[0].get_text(strip=True))

    return output