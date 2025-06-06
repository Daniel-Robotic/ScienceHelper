import json
from pathlib import Path
from tempfile import TemporaryDirectory

from nicegui import ui
import pandas as pd

from science_helper.search_vak_articles import (
    bool_to_yes_no,
    filter_rows_by_specialty,
    load_json,
)
from science_helper.utils import setting


temp_dir = TemporaryDirectory()


def science_articles_page() -> None:  # noqa: C901, D103, PLR0915
    data_dir = Path(setting.MAIN_DIRECTORY) / setting.DATA_DIRECTORY
    required_files = [
        data_dir / setting.SPECIALIZATION_NAME,
        data_dir / "vak_articles.json",
        data_dir / "whitelist_articles.json",
    ]

    if not all(p.exists() for p in required_files):
        with ui.column().classes("w-full items-center gap-4"):
            ui.label("Анализ научных журналов").classes("text-xl")
            ui.label("❌ Не найдены необходимые данные.").style("color:#e53935")
            ui.markdown("- Специализации\n- Журналы ВАК\n- Белый список")
        return

    taxonomy = json.loads(required_files[0].read_text(encoding="utf-8"))
    def get_cat():
        return ["Выбрать..."] + [c["category_name"] for c in taxonomy]
    def get_sub(c):
        return ["Выбрать..."] + [
            s["subcategory_name"]
            for s in next((x for x in taxonomy if x["category_name"] == c["label"]), {}).get(
                "sub_category", []
            )
        ]

    def get_specs(cat, sub):
        c = next((x for x in taxonomy if x["category_name"] == cat["label"]), None)
        sub = (
            next((s for s in c["sub_category"] if s["subcategory_name"] == sub["label"]), None)
            if c
            else None
        )
        return sub["values"] if sub else []

    def codes(selected):
        return sorted({".".join(s["label"].split(".")[:3]) for s in selected})

    def stringify_lists(rows):
        return [{k: ", ".join(v) if isinstance(v, list) else v for k, v in r.items()} for r in rows]

    with ui.column().classes("w-full items-center gap-4"):
        ui.label("Анализ научных журналов").classes("text-xl")

        cat_sel = ui.select(get_cat(), label="Категория").classes("w-96")
        sub_box = ui.column().classes("w-96 hidden")
        spec_box = ui.column().classes("w-96 hidden")

        run_btn = ui.button("АНАЛИЗИРОВАТЬ").props("color=primary").classes("hidden")
        spin = ui.spinner(size="lg").props("color=primary").classes("hidden mt-2")

        btn_row = ui.row().classes("w-full gap-3")
        tbl_wrap = ui.column().classes("w-full")
        dl_btn = (
            ui.button("⬇ Скачать Excel").props("color=secondary").classes("mt-2 self-start hidden")
        )

        active = {"btn": None}

        def highlight(b):
            if active["btn"]:
                active["btn"].props("color=secondary").update()
            b.props("color=primary").update()
            active["btn"] = b

        def show_table(rows, columns, xlsx_path):
            tbl_wrap.clear()
            with tbl_wrap:
                ui.table(
                    columns=columns, rows=rows, pagination=10, row_key=columns[0]["field"]
                ).classes("w-full").style("table-layout:fixed;word-break:break-word;")

            dl_btn.classes(remove="hidden")
            dl_btn.on("click", lambda: ui.download(str(xlsx_path), filename=xlsx_path.name))

        async def run():
            if not specs_selected:
                ui.notify("Выберите хотя бы одну специализацию")
                return

            run_btn.disable()
            spin.classes(remove="hidden")
            btn_row.clear()
            tbl_wrap.clear()

            vak_articles = load_json(data_dir / "vak_articles.json")
            vak_filters = filter_rows_by_specialty(vak_articles, codes(specs_selected))
            whitelist = load_json(data_dir / "whitelist_articles.json")

            data = []
            for it in vak_filters:
                hit = next((w for w in whitelist if it["issn"] in w["issns"]), None)
                if hit:
                    data.append(
                        {
                            "ВАК ID": it["N"],
                            "Наименование журнала": ", ".join(hit["title"]),
                            "issns": ", ".join(hit["issns"]),
                            "Специализации": ", ".join(it["specialties"]),
                            "Уровень журнала": hit["level"],
                            "WOS": bool_to_yes_no(hit["wos_cc"]["value"]),
                            "Scopus": bool_to_yes_no(hit["scopus"]["value"]),
                            "RSCI": bool_to_yes_no(hit["rsci"]["value"]),
                        }
                    )

            xlsx_dir = Path(temp_dir.name)
            xlsx_data = xlsx_dir / "data.xlsx"
            xlsx_filters = xlsx_dir / "filters.xlsx"
            xlsx_articles = xlsx_dir / "articles.xlsx"
            pd.DataFrame(data).to_excel(xlsx_data, index=False)
            pd.DataFrame(vak_filters).to_excel(xlsx_filters, index=False)
            pd.DataFrame(vak_articles).to_excel(xlsx_articles, index=False)

            # Определения колонок
            cols_data = [
                {
                    "name": "ВАК ID",
                    "label": "ID",
                    "field": "ВАК ID",
                    "align": "center",
                    "headerClasses": "text-center",
                    "style": "width:70px; white-space:normal;",
                },
                {
                    "name": "Наименование журнала",
                    "label": "Журнал",
                    "field": "Наименование журнала",
                    "headerClasses": "text-center",
                    "style": "max-width:280px; white-space:normal;",
                },
                {
                    "name": "issns",
                    "label": "ISSN",
                    "field": "issns",
                    "align": "center",
                    "headerClasses": "text-center",
                    "style": "width:120px; white-space:normal;",
                },
                {
                    "name": "Специализации",
                    "label": "Специализации",
                    "field": "Специализации",
                    "headerClasses": "text-center",
                    "style": "max-width:320px; white-space:normal;",
                },
                {
                    "name": "Уровень журнала",
                    "label": "Уровень",
                    "field": "Уровень журнала",
                    "headerClasses": "text-center",
                    "style": "width:90px;",
                },
                {
                    "name": "WOS",
                    "label": "WOS",
                    "field": "WOS",
                    "align": "center",
                    "headerClasses": "text-center",
                    "style": "width:70px;",
                },
                {
                    "name": "Scopus",
                    "label": "Scopus",
                    "field": "Scopus",
                    "align": "center",
                    "headerClasses": "text-center",
                    "style": "width:70px;",
                },
                {
                    "name": "RSCI",
                    "label": "RSCI",
                    "field": "RSCI",
                    "align": "center",
                    "headerClasses": "text-center",
                    "style": "width:70px;",
                },
            ]

            cols_simple = [
                {
                    "name": "N",
                    "label": "ID",
                    "field": "N",
                    "align": "center",
                    "headerClasses": "text-center",
                    "style": "width:60px;",
                },
                {
                    "name": "title",
                    "label": "Название",
                    "field": "title",
                    "headerClasses": "text-center",
                    "style": "max-width:320px; white-space:normal;",
                },
                {
                    "name": "issn",
                    "label": "ISSN",
                    "field": "issn",
                    "align": "center",
                    "headerClasses": "text-center",
                    "style": "width:120px;",
                },
                {
                    "name": "specialties",
                    "label": "Специализации",
                    "field": "specialties",
                    "headerClasses": "text-center",
                    "style": "max-width:340px; white-space:normal;",
                },
            ]

            with btn_row:
                b_art = ui.button(
                    "ВАК-статьи",
                    on_click=lambda: [
                        show_table(stringify_lists(vak_articles), cols_simple, xlsx_articles),
                        highlight(b_art),
                    ],
                ).props("color=secondary")
                b_flt = ui.button(
                    "Фильтр",
                    on_click=lambda: [
                        show_table(stringify_lists(vak_filters), cols_simple, xlsx_filters),
                        highlight(b_flt),
                    ],
                ).props("color=secondary")
                b_res = ui.button(
                    "Результат",
                    on_click=lambda: [show_table(data, cols_data, xlsx_data), highlight(b_res)],
                ).props("color=secondary")

            highlight(b_res)
            show_table(data, cols_data, xlsx_data)
            spin.classes(add="hidden")
            run_btn.enable()

        specs_selected: list[dict] = []

        def show_spec(opts):
            spec_box.clear()
            if not opts:
                return
            spec_box.classes(remove="hidden")
            run_btn.classes(remove="hidden")
            specs_selected.clear()
            ui.select(opts, label="Научные специальности", multiple=True).classes("w-96").on(
                "update:model-value",
                lambda e: (specs_selected.clear(), specs_selected.extend(e.args)),
            )

        def sub_changed(cat):
            if cat["label"] == "Выбрать...":
                sub_box.classes("hidden")
                spec_box.clear()
                return
            sub_box.classes(remove="hidden")
            spec_box.classes(add="hidden")
            run_btn.classes(add="hidden")
            sub_box.clear()

            def on_sub(e):
                sub = e.args
                if sub["label"] == "Выбрать...":
                    spec_box.clear()
                    return
                show_spec(get_specs(cat, sub))

            with sub_box:
                ui.select(get_sub(cat), label="Подкатегория").classes("w-96").on(
                    "update:model-value", on_sub
                )

        cat_sel.on("update:model-value", lambda e: sub_changed(e.args))
        run_btn.on("click", run)
