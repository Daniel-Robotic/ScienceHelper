import io
from nicegui import ui
from PIL import Image
from pathlib import Path

def image_processing_page():

    uploaded_images: dict[str, Image.Image] = {}

    def handle_upload(e):
        allowed_ext = ('.png', '.jpg', '.jpeg')
        if not e.name.lower().endswith(allowed_ext):
            ui.notify("Неподдерживаемый формат", type='negative')
            return

        e.content.seek(0)
        img = Image.open(io.BytesIO(e.content.read()))
        uploaded_images[e.name] = img
        ui.notify(f"{e.name} загружен")

    # ───────────────────────────────
    # UI: загрузка, обработка, скачивание
    # ───────────────────────────────
    
    img = Image.new("RGB", (100, 100), "#808080")
    ui.image(img).classes('w-64')

    ui.upload(
        on_upload=handle_upload,
        label='Загрузить изображение',
        auto_upload=True,
        multiple=True,
        max_file_size=5 * 1024 * 1024
    ).props('accept=.png,.jpg,.jpeg').classes('max-w-full')

    # ui.button('Обработать изображение', on_click=process_image).classes('mt-2')
    # ui.button('Скачать результат', on_click=download.download).classes('mt-2')
