import asyncio
from pathlib import Path

from nicegui import ui

from science_helper.search_vak_articles import (
    NomenclatureParser,
    PDFDownloader,
    PDFParser,
    save_to_json,
)
from science_helper.utils import setting


regex_values: dict[str, ui.input] = {}
web_values: dict[str, ui.input] = {}
dir_values: dict[str, ui.input] = {}

admin_container: ui.column | None = None
use_admin_checkbox: ui.checkbox | None = None

save_btn: ui.button | None = None
spec_btn: ui.button | None = None
download_btn: ui.button | None = None


def _toggle_buttons(state: bool) -> None:
    for btn in (save_btn, spec_btn, download_btn):
        if btn:
            if state:
                btn.enable()
                btn.props(remove="loading")
            else:
                btn.disable()
                btn.props("loading")


def admin_setting(state: bool) -> None:  # noqa: D103
    global admin_container  # noqa: PLW0602
    if not admin_container:
        return
    admin_container.clear()
    if state:
        with admin_container:
            ui.input("Логин", value=setting.ADMIN_LOGIN).classes("w-full").props("readonly")
            ui.input("Пароль", value=setting.ADMIN_PASSWORD, password=True).classes("w-full").props(
                "readonly"
            )


async def on_load_specializations(update_data_status: callable, refresh_analysis: callable) -> None:  # noqa: D103
    _toggle_buttons(False)
    try:
        parser = NomenclatureParser()
        specializations = await asyncio.to_thread(
            parser.get_specialties, setting.SPECIALIZATION_URL
        )
        out_path = (
            Path(setting.MAIN_DIRECTORY) / setting.DATA_DIRECTORY / setting.SPECIALIZATION_NAME
        )
        save_to_json(specializations, out_path)
        ui.notify("Специализации успешно загружены", timeout=300)
        update_data_status()
        refresh_analysis()
    finally:
        _toggle_buttons(True)


async def _download_and_parse_pdf() -> str | None:
    out_path = Path(setting.MAIN_DIRECTORY) / setting.DATA_DIRECTORY
    downloader = PDFDownloader(output_dir=out_path, config_path="config.ini")

    vak_path = await asyncio.to_thread(downloader.download_pdf_if_needed, setting.VAK_LIST_URL)
    if vak_path and vak_path.is_file():
        parser = PDFParser(vak_path)
        parsed_data = await asyncio.to_thread(parser.parse)
        save_to_json(parsed_data, out_path / "vak_articles.json")
        await asyncio.to_thread(
            downloader.dict_from_web, setting.WHITE_LIST_URL, "whitelist_articles.json"
        )
        return vak_path.name
    return None


async def on_download_pdf(update_data_status: callable, refresh_analysis: callable) -> None:  # noqa: D103
    _toggle_buttons(False)
    try:
        success = await _download_and_parse_pdf()
        if success:
            ui.notify("Журналы успешно загружены", timeout=300)
            update_data_status()
            refresh_analysis()
        else:
            ui.notify("Файл PDF не найден или недоступен", timeout=10)
    finally:
        _toggle_buttons(True)


def settings_page(update_data_status: callable, refresh_analysis: callable) -> None:  # noqa: D103
    global admin_container, use_admin_checkbox, save_btn, spec_btn, download_btn  # noqa: PLW0603

    with ui.row().classes("w-full justify-center"):
        with ui.row().classes("w-10/12 justify-between"):
            with ui.column().classes("w-1/4"):
                ui.label("REGEX настройки").classes("text-lg font-bold")
                for key, val in setting.config["REGEX"].items():
                    regex_values[key] = ui.input(label=key, value=val).classes("w-full")

            with ui.column().classes("w-1/4"):
                ui.label("WEB настройки").classes("text-lg font-bold")
                web_values["white_list_url"] = ui.input(
                    "Ссылка на белый список (json)", value=setting.WHITE_LIST_URL
                ).classes("w-full")
                web_values["vak_list_url"] = ui.input(
                    "Ссылка на список ВАК (pdf)", value=setting.VAK_LIST_URL
                ).classes("w-full")
                web_values["spec_url"] = ui.input(
                    "Ссылка на специализации", value=setting.SPECIALIZATION_URL
                ).classes("w-full")

                state = setting.USE_ADMIN.strip().lower() == "true"
                use_admin_checkbox = ui.checkbox(
                    "Использовать админ панель?",
                    value=state,
                    on_change=lambda e: admin_setting(e.value),
                ).classes("w-full")
                admin_container = ui.column().classes("gap-2 mt-2")
                admin_setting(state)

            with ui.column().classes("w-1/4"):
                ui.label("Настройки директории").classes("text-lg font-bold")
                dir_values["main_dir"] = ui.input(
                    "Основная директория", value=setting.MAIN_DIRECTORY
                ).classes("w-full")
                dir_values["data_dir"] = ui.input(
                    "Директория с данными", value=setting.DATA_DIRECTORY
                ).classes("w-full")
                dir_values["spec_file"] = ui.input(
                    "Имя файла для специализаций", value=setting.SPECIALIZATION_NAME
                ).classes("w-full")
                dir_values["file_name"] = (
                    ui.input("Имя файла ВАК", value=setting.FILENAME)
                    .classes("w-full")
                    .props("readonly")
                )

    def on_save() -> None:
        config = {
            "regex": {k: v.value for k, v in regex_values.items()},
            "web": {k: v.value for k, v in web_values.items()},
            "directories": {k: v.value for k, v in dir_values.items()},
            "admin": {
                "enabled": use_admin_checkbox.value,
                "login": setting.ADMIN_LOGIN,
                "password": setting.ADMIN_PASSWORD,
            },
        }
        dir_values.items()
        setting.save_config(config)
        ui.notify("Настройки обновлены", timeout=3)

    with ui.row().classes("w-full justify-center mt-6 gap-4"):
        save_btn = ui.button("ОБНОВИТЬ НАСТРОЙКИ", on_click=on_save).props("color=primary")
        spec_btn = ui.button(
            "Загрузить специализации",
            on_click=lambda: on_load_specializations(update_data_status, refresh_analysis),
        ).props("color=primary")
        download_btn = ui.button(
            "Загрузить журналы",
            on_click=lambda: on_download_pdf(update_data_status, refresh_analysis),
        ).props("color=primary")
