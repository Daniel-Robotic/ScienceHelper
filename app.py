from pathlib import Path
from nicegui import ui
from pages.analysis_page import science_articles_page
from pages.settings_page import settings_page

# ────────────────────────────────
# Глобальное состояние
# ────────────────────────────────
data_ready = False

def check_data_ready():
    required_files = ['specializations.json', 'vak_articles.json', 'whitelist_articles.json']
    return all((Path('data') / name).exists() for name in required_files)

def update_data_status():
    global data_ready
    data_ready = check_data_ready()

# ────────────────────────────────
# Интерфейс
# ────────────────────────────────
@ui.page('/')
def main_page():
    update_data_status()  # при заходе на страницу проверим наличие данных

    with ui.header():
        ui.label('Научный хелпер :D').classes('text-xl')

    with ui.tabs().classes('w-full') as tabs:
        tab1 = ui.tab('Анализ')
        tab2 = ui.tab('Настройки')

    with ui.tab_panels(tabs, value=tab1).classes('w-full'):
        with ui.tab_panel(tab1):
            @ui.refreshable
            def science_panel():
                science_articles_page()  # всегда вызываем, логика проверки внутри страницы
            science_panel()

        with ui.tab_panel(tab2):
            settings_page(update_data_status, science_panel.refresh)


ui.run(title="BestScience", dark=False)
