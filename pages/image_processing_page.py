from nicegui import ui
from PIL import Image
import io
import base64
from pathlib import Path
from tempfile import TemporaryDirectory
from image_processing import ImagesDesign

# Хранилище временных параметров компоновки
united_params = {
    'layout': 'row',
    'spacing': 10,
    'bg_color': '#ffffff',
    'grid_cols': None,
    'grid_rows': None,
    'width': 512,
    'height': None,
}

# UI state variables для хранения ссылок на input элементы
united_controls = {}

# Допустимые значения layout
valid_layouts = {'row', 'column', 'grid'}

tmp_dir = TemporaryDirectory()
design = ImagesDesign(images_path=tmp_dir.name)

# Список шрифтов
font_dir = Path('./fonts')
font_files = sorted([f.stem for f in font_dir.glob('*.ttf') if f.is_file()])
signature_label_options = ['cyrillic_lower', 'cyrillic_upper', 'latin_lower', 'latin_upper', 'roman']
signature_pos_options = ['top-left', 'top-right', 'bottom-left', 'bottom-right']

def image_processing_page():
    with ui.column().classes('w-full items-center justify-center gap-4'):
        image_slot = ui.image().classes('w-1/2 rounded-xl shadow-lg')

        with ui.dialog() as upload_dialog, ui.card().classes('p-6'):
            ui.label('Загрузить изображения').classes('text-lg font-semibold')
            ui.upload(
                on_upload=lambda e: handle_upload(e, upload_dialog, image_slot, download_link),
                auto_upload=True, multiple=True, max_file_size=5 * 1024 * 1024
            ).props('accept=.png,.jpg,.jpeg').classes('max-w-full')
            ui.button('Закрыть', on_click=upload_dialog.close).props('flat color=secondary')

        with ui.row().classes('gap-4'):
            ui.button('📤 Загрузить', on_click=upload_dialog.open).props('color=primary')
            ui.button('🗑 Очистить', on_click=lambda: clear_images(image_slot)).props('color=negative')
            ui.button('📥 Скачать результат',
                      on_click=lambda: ui.run_javascript('document.getElementById("download_result").click();')) \
                .bind_visibility_from(image_slot, 'visible')

        global download_link
        download_link = ui.html('').classes('hidden')

        # Параметры обработки
        with ui.expansion('Параметры обработки', icon='settings'):
            with ui.grid(columns=4).classes('gap-4 w-full'):
                def safe_int(val, default=0):
                    try:
                        return int(val)
                    except ValueError:
                        return default

                ui.input('Размер рамки', value=str(design.border_size),
                         on_change=lambda e: update_param('border_size', safe_int(e.value), image_slot)).props('type=number')
                ui.color_input(label='Цвет рамки', value='#000000',
                               on_change=lambda e: update_param('border_fill', e.value, image_slot))
                ui.checkbox('Добавлять подпись', value=design.signature,
                            on_change=lambda e: update_param('signature', e.value, image_slot))
                ui.select(signature_label_options, value=design.signature_label,
                          label='Тип подписи',
                          on_change=lambda e: update_param('signature_label', e.value, image_slot))
                ui.color_input(label='Цвет надписи', value='#fff',
                               on_change=lambda e: update_param('signature_label_color', e.value, image_slot))
                ui.select(signature_pos_options, value=design.signature_pos,
                          label='Позиция подписи',
                          on_change=lambda e: update_param('signature_pos', e.value, image_slot))
                ui.input('Размер подписи (ширина)', value=str(design.signature_size[0]),
                         on_change=lambda e: update_param('signature_size', (safe_int(e.value), design.signature_size[1]), image_slot)).props('type=number')
                ui.input('Размер подписи (высота)', value=str(design.signature_size[1]),
                         on_change=lambda e: update_param('signature_size', (design.signature_size[0], safe_int(e.value)), image_slot)).props('type=number')
                ui.color_input(label='Цвет подписи (фон)', value='#000',
                               on_change=lambda e: update_param('signature_color', e.value, image_slot))
                ui.input('Размер шрифта подписи', value=str(design.signature_font_size),
                         on_change=lambda e: update_param('signature_font_size', safe_int(e.value), image_slot)).props('type=number')
                ui.checkbox('Показывать оси', value=design.draw_axis,
                            on_change=lambda e: update_param('draw_axis', e.value, image_slot))
                ui.input('Смещение осей', value=str(design.axis_offset),
                         on_change=lambda e: update_param('axis_offset', safe_int(e.value), image_slot)).props('type=number')
                ui.input('Длина осей', value=str(design.axis_length),
                         on_change=lambda e: update_param('axis_length', safe_int(e.value), image_slot)).props('type=number')
                ui.input('Толщина осей', value=str(design.axis_width),
                         on_change=lambda e: update_param('axis_width', safe_int(e.value), image_slot)).props('type=number')
                ui.input('Размер шрифта осей', value=str(design.axis_font_size),
                         on_change=lambda e: update_param('axis_font_size', safe_int(e.value), image_slot)).props('type=number')
                ui.select(font_files or ['Arial'], value=Path(design.font_family).stem,
                          label='Шрифт',
                          on_change=lambda e: update_param('font_family', f'./fonts/{e.value}.ttf', image_slot))

        with ui.expansion('Параметры компоновки', icon='grid_on'):
            with ui.grid(columns=4).classes('gap-4 w-full'):
                layout_select = ui.select(['row', 'column', 'grid'], value=united_params['layout'], label='Расположение')
                layout_select.on('update:model-value', lambda e: update_united('layout', e.args, image_slot))

                spacing_input = ui.input('Отступ между изображениями', value=str(united_params['spacing'])).props('type=number')
                spacing_input.on('change', lambda e: update_united('spacing', safe_int(e.args), image_slot))

                bg_color_picker = ui.color_input('Цвет фона', value=united_params['bg_color'])
                bg_color_picker.on('change', lambda e: update_united('bg_color', e.args, image_slot))

                grid_cols_input = ui.input('Число колонок (grid)', value='').props('type=number')
                grid_cols_input.on('change', lambda e: update_united('grid_cols', safe_int(e.args) if e.args else None, image_slot))

                grid_rows_input = ui.input('Число строк (grid)', value='').props('type=number')
                grid_rows_input.on('change', lambda e: update_united('grid_rows', safe_int(e.args) if e.args else None, image_slot))

                width_input = ui.input('Ширина изображения', value=str(united_params['width'])).props('type=number')
                width_input.on('change', lambda e: update_united('width', safe_int(e.args), image_slot))

                height_input = ui.input('Высота изображения', value='').props('type=number')
                height_input.on('change', lambda e: update_united('height', safe_int(e.args) if e.args else None, image_slot))

# Обработчики

def handle_upload(e, dialog, image_slot, download_link):
    allowed_ext = ('.png', '.jpg', '.jpeg')
    if not e.name.lower().endswith(allowed_ext):
        ui.notify("Неподдерживаемый формат", type='negative')
        return
    e.content.seek(0)
    img = Image.open(io.BytesIO(e.content.read())).convert("RGB")
    design.append(img)
    ui.notify(f"{e.name} загружен", type="positive")
    dialog.close()
    update_output(image_slot)

def clear_images(image_slot):
    design._images.clear()
    image_slot.set_source("")
    ui.notify("Изображения очищены", type="info")

def update_param(name, value, image_slot):
    setattr(design, name, value)
    update_output(image_slot)

def update_united(name, value, image_slot):
    if name == 'layout':
        if isinstance(value, dict) and 'label' in value:
            value = value['label']
        if value not in valid_layouts:
            ui.notify(f"Недопустимое значение layout: {value}", type='negative')
            return
    united_params[name] = value
    if len(design) > 1:
        update_output(image_slot)

def update_output(image_slot):
    if not len(design):
        return
    result = design.united_images(
        layout=united_params['layout'],
        spacing=united_params['spacing'],
        bg_color=united_params['bg_color'],
        grid_cols=united_params['grid_cols'],
        grid_rows=united_params['grid_rows'],
        width=united_params['width'],
        height=united_params['height'],
    )
    buffer = io.BytesIO()
    result.save(buffer, format="PNG")
    buffer.seek(0)
    b64 = base64.b64encode(buffer.getvalue()).decode()
    image_slot.set_source(f'data:image/png;base64,{b64}')
    download_link.set_content(f'''
        <a id="download_result" download="result.png" href="data:image/png;base64,{b64}"></a>
    ''')
