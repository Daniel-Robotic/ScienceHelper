import base64
import io
from pathlib import Path
from tempfile import TemporaryDirectory

from nicegui import ui
from PIL import Image

from science_helper.image_processing import (
    DrawioImageDesign,
    ImagesDesign,
    LabelMode,
    LayoutMode,
    SignaturePosition,
)


united_params = {
    "layout": "row",
    "spacing": 10,
    "bg_color": "#ffffff",
    "grid_cols": None,
    "grid_rows": None,
    "width": 512,
    "height": None,
}

united_controls = {}

valid_layouts = set([mode.value for mode in LayoutMode])

tmp_dir = TemporaryDirectory()
design = ImagesDesign(images_path=tmp_dir.name)

font_dir = Path("./fonts")
font_files = sorted([f.stem for f in font_dir.glob("*.ttf") if f.is_file()])
signature_label_options = [mode.value for mode in LabelMode]
signature_pos_options = [mode.value for mode in SignaturePosition]

download_link = ui.html("").classes("hidden")
download_drawio_link = ui.html("").classes("hidden")


def image_processing_page():  # noqa: D103, PLR0915
    with ui.column().classes("w-full items-center justify-center gap-4"):
        image_slot = ui.image().classes("w-1/2 rounded-xl shadow-lg")

        with ui.dialog() as upload_dialog, ui.card().classes("p-6"):
            ui.label("Загрузить изображения").classes("text-lg font-semibold")
            ui.upload(
                on_upload=lambda e: handle_upload(e, upload_dialog, image_slot, download_link),
                auto_upload=True,
                multiple=True,
                max_file_size=5 * 1024 * 1024,
            ).props("accept=.png,.jpg,.jpeg").classes("max-w-full")
            ui.button("Закрыть", on_click=upload_dialog.close).props("flat color=secondary")

        with ui.row().classes("gap-4"):
            ui.button("📤 Загрузить", on_click=upload_dialog.open).props("color=primary")
            ui.button("🗑 Очистить", on_click=lambda: clear_images(image_slot)).props(
                "color=negative"
            )
            ui.button("📥 Скачать .png", on_click=download_png).props(
                "color=primary"
            ).bind_visibility_from(image_slot, "visible")
            ui.button("📥 Скачать .drawio", on_click=download_drawio).props(
                "color=accent"
            ).bind_visibility_from(image_slot, "visible")

        download_link  # noqa: B018
        download_drawio_link  # noqa: B018

        with ui.expansion("Параметры обработки", icon="settings"):
            with ui.grid(columns=4).classes("gap-4 w-full"):

                def safe_int(val, default=0):
                    try:
                        return int(val)
                    except ValueError:
                        return default

                def safe_font(val: str, fallback: int = 12) -> int:
                    v = safe_int(val, fallback)
                    if v <= 0:
                        ui.notify("Размер шрифта должен быть положительным", type="warning")
                        return fallback
                    return v

                ui.input(
                    "Размер рамки",
                    value=str(design.border_size),
                    on_change=lambda e: update_param("border_size", safe_int(e.value), image_slot),
                ).props("type=number min=0")
                ui.color_input(
                    label="Цвет рамки",
                    value="#000000",
                    on_change=lambda e: update_param("border_fill", e.value, image_slot),
                )

                ui.checkbox(
                    "Добавлять подпись",
                    value=design.signature,
                    on_change=lambda e: update_param("signature", e.value, image_slot),
                )
                ui.select(
                    signature_label_options,
                    value=design.signature_label,
                    label="Тип подписи",
                    on_change=lambda e: update_param("signature_label", e.value, image_slot),
                )
                ui.color_input(
                    label="Цвет надписи",
                    value="#fff",
                    on_change=lambda e: update_param("signature_label_color", e.value, image_slot),
                )
                ui.select(
                    signature_pos_options,
                    value=design.signature_pos,
                    label="Позиция подписи",
                    on_change=lambda e: update_param("signature_pos", e.value, image_slot),
                )
                ui.input(
                    "Размер подписи (ширина)",
                    value=str(design.signature_size[0]),
                    on_change=lambda e: update_param(
                        "signature_size", (safe_int(e.value), design.signature_size[1]), image_slot
                    ),
                ).props("type=number min=0")
                ui.input(
                    "Размер подписи (высота)",
                    value=str(design.signature_size[1]),
                    on_change=lambda e: update_param(
                        "signature_size", (design.signature_size[0], safe_int(e.value)), image_slot
                    ),
                ).props("type=number min=0")
                ui.color_input(
                    label="Цвет подписи (фон)",
                    value="#000",
                    on_change=lambda e: update_param("signature_color", e.value, image_slot),
                )
                ui.input(
                    "Размер шрифта подписи",
                    value=str(design.signature_font_size),
                    on_change=lambda e: update_param(
                        "signature_font_size", safe_int(e.value), image_slot
                    ),
                ).props("type=number min=3")

                ui.checkbox(
                    "Показывать оси",
                    value=design.draw_axis,
                    on_change=lambda e: update_param("draw_axis", e.value, image_slot),
                )
                ui.input(
                    "Подписи оси X",
                    value=design.axis_labels[0]
                    if isinstance(design.axis_labels[0], str)
                    else ",".join(design.axis_labels[0]),
                    on_change=lambda e: update_axis_labels("x", e.value, image_slot),
                )
                ui.input(
                    "Подписи оси Y",
                    value=design.axis_labels[1]
                    if isinstance(design.axis_labels[1], str)
                    else ",".join(design.axis_labels[1]),
                    on_change=lambda e: update_axis_labels("y", e.value, image_slot),
                )
                ui.input(
                    "Смещение по X",
                    value=str(
                        design.axis_offset[0]
                        if isinstance(design.axis_offset, tuple)
                        else design.axis_offset
                    ),
                    on_change=lambda e: update_axis_offset("x", e.value, image_slot),
                ).props("type=number min=0")
                ui.input(
                    "Смещение по Y",
                    value=str(
                        design.axis_offset[1]
                        if isinstance(design.axis_offset, tuple)
                        else design.axis_offset
                    ),
                    on_change=lambda e: update_axis_offset("y", e.value, image_slot),
                ).props("type=number min=0")
                ui.input(
                    "Длина осей",
                    value=str(design.axis_length),
                    on_change=lambda e: update_param("axis_length", safe_int(e.value), image_slot),
                ).props("type=number min=1")
                ui.input(
                    "Толщина осей",
                    value=str(design.axis_width),
                    on_change=lambda e: update_param("axis_width", safe_int(e.value), image_slot),
                ).props("type=number min=1")
                ui.input(
                    "Размер шрифта осей",
                    value=str(design.axis_font_size),
                    on_change=lambda e: update_param(
                        "axis_font_size", safe_int(e.value), image_slot
                    ),
                ).props("type=number min=3")
                ui.select(
                    font_files or ["Arial"],
                    value=design.font_family,
                    label="Шрифт",
                    on_change=lambda e: update_param("font_family", e.value, image_slot),
                )

        with ui.expansion("Параметры компоновки", icon="grid_on"):
            with ui.grid(columns=4).classes("gap-4 w-full"):
                layout_select = ui.select(
                    ["row", "column", "grid"], value=united_params["layout"], label="Расположение"
                )
                layout_select.on(
                    "update:model-value", lambda e: update_united("layout", e.args, image_slot)
                )

                spacing_input = ui.input(
                    "Отступ между изображениями", value=str(united_params["spacing"])
                ).props("type=number")
                spacing_input.on(
                    "change", lambda e: update_united("spacing", safe_int(e.args), image_slot)
                )

                bg_color_picker = ui.color_input("Цвет фона", value=united_params["bg_color"])
                bg_color_picker.on(
                    "change", lambda e: update_united("bg_color", e.args, image_slot)
                )

                grid_cols_input = ui.input("Число колонок (grid)", value="").props("type=number")
                grid_cols_input.on(
                    "change",
                    lambda e: update_united(
                        "grid_cols", safe_int(e.args) if e.args else None, image_slot
                    ),
                )

                grid_rows_input = ui.input("Число строк (grid)", value="").props("type=number")
                grid_rows_input.on(
                    "change",
                    lambda e: update_united(
                        "grid_rows", safe_int(e.args) if e.args else None, image_slot
                    ),
                )

                width_input = ui.input(
                    "Ширина изображения", value=str(united_params["width"])
                ).props("type=number")
                width_input.on(
                    "change", lambda e: update_united("width", safe_int(e.args), image_slot)
                )

                height_input = ui.input("Высота изображения", value="").props("type=number")
                height_input.on(
                    "change",
                    lambda e: update_united(
                        "height", safe_int(e.args) if e.args else None, image_slot
                    ),
                )


# Обработчики
def update_axis_offset(axis: str, value: str, image_slot):  # noqa: D103
    try:
        offset = int(value)
        current = design.axis_offset
        if isinstance(current, int):
            current = (current, current)

        if axis == "x":
            new_offset = (offset, current[1])
        else:
            new_offset = (current[0], offset)

        update_param("axis_offset", new_offset, image_slot)
    except ValueError:
        ui.notify(f"Смещение по оси {axis.upper()} должно быть числом", type="warning")


def update_axis_labels(axis: str, text: str, image_slot):  # noqa: D103
    try:
        values = [v.strip() for v in text.split(",") if v.strip()]
        if not values:
            ui.notify(f"Поле оси {axis.upper()} пусто", type="warning")
            return

        parsed_value: str | tuple[str, ...] = values[0] if len(values) == 1 else tuple(values)

        if isinstance(parsed_value, tuple) and len(parsed_value) != len(design):
            ui.notify(
                f"Количество подписей для оси {axis.upper()} должно быть {len(design)}",
                type="negative",
            )
            return

        current_x, current_y = design.axis_labels
        if axis == "x":
            design.axis_labels = (parsed_value, current_y)
        else:
            design.axis_labels = (current_x, parsed_value)

        update_output(image_slot)
    except Exception as ex:
        ui.notify(f"Ошибка при установке подписей осей: {ex}", type="negative")


def handle_upload(e, dialog, image_slot, download_link):  # noqa: D103
    allowed_ext = (".png", ".jpg", ".jpeg")
    if not e.name.lower().endswith(allowed_ext):
        ui.notify("Неподдерживаемый формат", type="negative")
        return
    e.content.seek(0)
    img = Image.open(io.BytesIO(e.content.read())).convert("RGB")
    design.append(img)
    ui.notify(f"{e.name} загружен", type="positive")
    dialog.close()
    update_output(image_slot)


def clear_images(image_slot):  # noqa: D103
    design._images.clear()
    image_slot.set_source("")
    ui.notify("Изображения очищены", type="info")


def update_param(name, value, image_slot):  # noqa: D103
    setattr(design, name, value)
    update_output(image_slot)


def update_united(name, value, image_slot):  # noqa: D103
    if name == "layout":
        if isinstance(value, dict) and "label" in value:
            value = value["label"]
        if value not in valid_layouts:
            ui.notify(f"Недопустимое значение layout: {value}", type="negative")
            return
    united_params[name] = value
    if len(design) > 1:
        update_output(image_slot)


def update_output(image_slot):  # noqa: D103
    if not len(design):
        return
    result = design.united_images(
        layout=united_params["layout"],
        spacing=united_params["spacing"],
        bg_color=united_params["bg_color"],
        grid_cols=united_params["grid_cols"],
        grid_rows=united_params["grid_rows"],
        width=united_params["width"],
        height=united_params["height"],
    )
    buffer = io.BytesIO()
    result.save(buffer, format="PNG")
    buffer.seek(0)
    b64 = base64.b64encode(buffer.getvalue()).decode()
    image_slot.set_source(f"data:image/png;base64,{b64}")
    download_link.set_content(f"""
        <a id="download_result" download="result.png" href="data:image/png;base64,{b64}"></a>
    """)


def download_png():  # noqa: D103
    if not len(design):
        ui.notify("Нет изображений для сохранения", type="warning")
        return

    try:
        result = design.united_images(
            layout=united_params["layout"],
            spacing=united_params["spacing"],
            bg_color=united_params["bg_color"],
            grid_cols=united_params["grid_cols"],
            grid_rows=united_params["grid_rows"],
            width=united_params["width"],
            height=united_params["height"],
        )
        output_path = Path(tmp_dir.name) / "result.png"
        result.save(output_path, format="PNG")
        ui.download(str(output_path), filename="result.png")
    except Exception as e:
        ui.notify(f"Ошибка при сохранении PNG: {e}", type="negative")


def download_drawio():  # noqa: D103
    if not len(design):
        ui.notify("Нет изображений для сохранения", type="warning")
        return
    try:
        drawio = DrawioImageDesign(images_path=tmp_dir.name)
        drawio._images = design._images.copy()

        drawio.border_size = design.border_size
        drawio.border_fill = design.border_fill
        drawio.signature = design.signature
        drawio.signature_label = design.signature_label
        drawio.signature_label_color = design.signature_label_color
        drawio.signature_color = design.signature_color
        drawio.signature_font_size = design.signature_font_size
        drawio.signature_size = design.signature_size
        drawio.signature_pos = design.signature_pos
        drawio.axis_labels = design.axis_labels
        drawio.axis_length = design.axis_length
        drawio.axis_width = design.axis_width
        drawio.axis_font_size = design.axis_font_size
        drawio.axis_offset = design.axis_offset
        drawio.font_family = design.font_family
        drawio.draw_axis = design.draw_axis

        output_path = Path(tmp_dir.name) / "result.drawio"

        drawio.export_to_drawio(
            file=output_path,
            layout=united_params["layout"],
            spacing=united_params["spacing"],
            grid_cols=united_params["grid_cols"],
            grid_rows=united_params["grid_rows"],
            width=united_params["width"],
            height=united_params["height"],
        )

        ui.download(str(output_path), filename="result.drawio")
    except Exception as e:
        ui.notify(f"Ошибка при сохранении drawio: {e}", type="negative")
