<!-- Project logo -->
<p align="center">
  <img src="web/static/logo.png" alt="Science Helper" width="120"/>
</p>

<h1 align="center">Science Helper</h1>
<p align="center">
  <em>A toolkit for automating scientific writing &amp; visualization</em><br>
  <a href="#-features">Features</a> •
  <a href="#-quick-start">Quick&nbsp;Start</a> •
  <a href="#-docker">Docker</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-repository-structure">Structure</a> •
  <a href="#-roadmap">Roadmap</a> •
  <a href="#-license">License</a>
</p>

> ⚠️ **Science Helper** is under active development (v0.1.0). API &amp; UI may change.

---

## 🚀 Features

| Module | Purpose | Key APIs |
|--------|---------|----------|
| **Image Processor** | Combines images into PNG or `.drawio`, adds labels/axes | `ImagesDesign`, `DrawioImageDesign` |
| **Journal Parser** | Downloads & parses VAK journal lists, filters by specialties and checks white‑list | `PDFDownloader`, `PDFParser`, `NomenclatureParser`, `filter_rows_by_specialty` |
| **NiceGUI UI** | Web interface: “Images”, “Parsing”, “Settings” | `image_processing_page`, `analysis_page`, `settings_page` |

### 🖼 Image Processing
* Layouts: `row`, `column`, `grid`
* Labels: Latin/Cyrillic, Arabic/Roman numerals or custom set  
* Coordinate axes with adjustable labels/offset  
* Export to **PNG** & **Draw.io**

### 📑 Journal Analysis
* Async download of VAK PDF & white‑list (JSON)  
* PDF parsing (no OCR) via regex  
* HTML table parsing for specialties  
* Journal filtering + Excel export

### ⚙️ Settings
* Sections **REGEX / WEB / Directories**  
* Optional admin panel (login/password) ⚙️ (in development)  
* Buttons “Download journals” & “Download specialties”  

---

## ⏱ Quick Start

```bash
git clone https://github.com/<your_username>/science-helper.git
cd science-helper
pip install -r requirements.txt
python main.py          # UI → http://localhost:8080
```

---

## 🐳 Docker

> Build the image:  
> `docker build -t science-helper .`

(Or pull ready‑made: `ghcr.io/daniel-robotic/science-helper:latest`)

---

## 🏗 Architecture

```text
┌─────────────┐
│  NiceGUI UI │──┐
└─────────────┘  │  internal HTTP calls
	  ▼          │
┌───────────────┐│      ┌──────────────────────┐
│ image_processing │────►│  image_processing/   │
└───────────────┘│      └──────────────────────┘
	  ▼          │
┌────────────────┴──────┐
│ search_vak_articles   │  (PDF/HTML parsers)
└───────────────────────┘
```

---

## 📁 Repository Structure

```
science-helper/
├─ science_helper/
│  ├─ image_processing/      # ImagesDesign, DrawioImageDesign, enums
│  ├─ search_vak_articles/   # PDFDownloader, PDFParser, ...
│  └─ utils/setting.py
├─ web/
│  ├─ pages/                 # NiceGUI pages
│  └─ static/                # logo & favicon
├─ data/                     # downloaded PDF/JSON
├─ fonts/
├─ config.ini
├─ requirements.txt
└─ main.py
```

---

## 🗺 Roadmap
- [ ] Bibliography formatting (plain text)
- [ ] Bibliography formatting (via URL)
- [ ] Custom diagram DSL with export to `.drawio`

---

## 🤝 Contribution

PRs & issues are welcome!  
Before committing run:

```bash
ruff check .
pytest -q
```

---

## 📜 License

[MIT](LICENSE) © Daniel Grabar, 2025

---

# 🇷🇺 Русская версия

<p align="center">
  <em>Набор инструментов для автоматизации оформления научных работ</em><br>
  <a href="#-возможности">Возможности</a> •
  <a href="#️-быстрый-старт">Быстрый старт</a> •
  <a href="#-docker">Docker</a> •
  <a href="#-архитектура">Архитектура</a> •
  <a href="#-структура-репозитория">Структура</a> •
  <a href="#-дорожная-карта">Дорожная карта</a> •
  <a href="#-лицензия">Лицензия</a>
</p>

> ⚠️ **Science Helper** находится в активной разработке (v0.1.0). API и интерфейс могут меняться.

---

## 🚀 Возможности

| Модуль | Что делает | Ключевые API |
|--------|------------|--------------|
| **Обработчик изображений** | Объединяет картинки в PNG или `.drawio`, добавляет подписи/оси | `ImagesDesign`, `DrawioImageDesign` |
| **Парсинг журналов** | Скачивает и парсит списки ВАК‑журналов, фильтрует по специальностям и проверяет их в белом списке | `PDFDownloader`, `PDFParser`, `NomenclatureParser`, `filter_rows_by_specialty` |
| **NiceGUI UI** | Веб‑интерфейс: «Изображения», «Парсинг», «Настройки» | `image_processing_page`, `analysis_page`, `settings_page` |

### 🖼 Обработка изображений
* Макеты: `row`, `column`, `grid`
* Подписи: латиница/кириллица, арабские/римские цифры или кастомный набор  
* Координатные оси с гибкими подписью/смещением  
* Экспорт в **PNG** и **Draw.io**

### 📑 Анализ научных журналов
* Асинхронная загрузка PDF‑списка ВАК и «белого списка» (JSON)  
* Парсинг PDF (без OCR) по регулярным выражениям  
* Парсинг HTML‑таблицы специальностей  
* Фильтрация журналов + экспорт в Excel

### ⚙️ Настройки
* Разделы **REGEX / WEB / Директории**  
* Опциональная админ‑панель (логин/пароль) ⚙️ (в разработке)  
* Кнопки «Загрузить журналы» и «Загрузить специализации»  

---

## ⏱️ Быстрый старт

```bash
git clone https://github.com/<your_username>/science-helper.git
cd science-helper
pip install -r requirements.txt
python main.py            # UI → http://localhost:8080
```

---

## 🐳 Docker

> Для сборки образа выполните:  
> `docker build -t science-helper .`

(Готовый образ: `ghcr.io/daniel-robotic/science-helper:latest`)

---

## 🏗 Архитектура
```text
┌─────────────┐
│  NiceGUI UI │──┐
└─────────────┘  │  HTTP / внутренние вызовы
	  ▼          │
┌───────────────┐│      ┌──────────────────────┐
│ image_processing │────►│  image_processing/   │
└───────────────┘│      └──────────────────────┘
	  ▼          │
┌────────────────┴──────┐
│ search_vak_articles   │  (PDF/HTML парсеры)
└───────────────────────┘
```

---

## 📁 Структура репозитория
```
science-helper/
├─ science_helper/
│  ├─ image_processing/
│  ├─ search_vak_articles/
│  └─ utils/setting.py
├─ web/
│  ├─ pages/
│  └─ static/
├─ data/
├─ fonts/
├─ config.ini
├─ requirements.txt
└─ main.py
```

---

## 🗺 Дорожная карта
- [ ] Оформление списка литературы (текстом)  
- [ ] Оформление списка литературы (по ссылке)  
- [ ] DSL для диаграмм и блок‑схем с экспортом в `.drawio`

---

## 🤝 Вклад
PR и issue приветствуются!  

```bash
ruff check .
pytest -q
```

---

## 📜 Лицензия

[MIT](LICENSE) © Daniel Grabar, 2025
