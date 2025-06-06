from pathlib import Path

from nicegui import ui

from web.pages.analysis_page import science_articles_page
from web.pages.image_processing_page import image_processing_page
from web.pages.settings_page import settings_page


data_ready = False


def check_data_ready():  # noqa: D103
    required_files = ["specializations.json", "vak_articles.json", "whitelist_articles.json"]
    return all((Path("data") / name).exists() for name in required_files)


def update_data_status():  # noqa: D103
    global data_ready  # noqa: PLW0603
    data_ready = check_data_ready()


@ui.page("/")
def main_page():  # noqa: D103
    update_data_status()  # при заходе на страницу проверим наличие данных

    with ui.header().classes("items-center justify-between p-4 shadow-md"):
        with ui.row().classes("items-center gap-4"):
            with ui.link(target="/"):
                ui.image("./web/static/logo.png").classes("w-12 h-12")
            ui.label("Science Helper").classes("text-xl font-bold")

    with ui.tabs().classes("w-full") as tabs:
        tab1 = ui.tab("Обработчик изображений")
        tab2 = ui.tab("Парсинг статей")
        tab3 = ui.tab("Настройки")

    with ui.tab_panels(tabs, value=tab1).classes("w-full"):
        with ui.tab_panel(tab1):

            @ui.refreshable
            def image_processing_panel():
                image_processing_page()

            image_processing_panel()

        with ui.tab_panel(tab2):

            @ui.refreshable
            def science_panel():
                science_articles_page()

            science_panel()

        with ui.tab_panel(tab3):
            settings_page(update_data_status, science_panel.refresh)


ui.run(title="ScienceHelper", favicon="./web/static/favicon.ico")
