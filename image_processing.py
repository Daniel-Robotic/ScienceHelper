import math
from enum import Enum
from PIL import Image, ImageOps, ImageDraw, ImageFont
from pathlib import Path
from typing import List, Optional, Tuple
from image_processing import ISOPage, PageSeries, Orientation, ColorMode, LayoutMode



def to_roman(n: int) -> str:
    """
    Переводит число в римскую цифру.
    """
    val = [
        1000, 900, 500, 400,
        100, 90, 50, 40,
        10, 9, 5, 4, 1
    ]
    syms = [
        'M', 'CM', 'D', 'CD',
        'C', 'XC', 'L', 'XL',
        'X', 'IX', 'V', 'IV', 'I'
    ]
    roman = ''
    for i in range(len(val)):
        count = n // val[i]
        roman += syms[i] * count
        n -= val[i] * count
    return roman



def get_label(index: int, mode: str = "cyrillic") -> str:
    """
    Возвращает подпись по индексу:
    - mode: 'latin', 'cyrillic', 'arabic', 'roman'
    """
    if mode == "latin":
        return chr(ord('A') + index)  # A, B, C, ...
    elif mode == "cyrillic":
        # Пропускаем Ё, идём по алфавиту
        alphabet = [chr(code) for code in range(ord('А'), ord('А') + 32)]
        if index >= len(alphabet):
            raise ValueError("Слишком большой индекс для кириллицы")
        return alphabet[index]
    elif mode == "arabic":
        return str(index + 1)  # 1, 2, ...
    elif mode == "roman":
        return to_roman(index + 1)  # I, II, III, ...
    else:
        raise ValueError("Неверный режим: 'latin', 'cyrillic', 'arabic', 'roman'")

def add_axes(img: Image.Image,
             label_x: str = "X",
             label_y: str = "Y",
             axis_color: str = "black",
             font_size: int = 20,
             arrow_len: int = 60,
             offset: int = 20) -> Image.Image:
    """
    Добавляет стрелки и подписи по осям X (вправо) и Y (вверх).
    """
    img = img.copy()
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    w, h = img.size

    # Ось X (слева направо)
    x0 = offset
    y0 = h - offset
    x1 = x0 + arrow_len
    y1 = y0
    draw.line((x0, y0, x1, y1), fill=axis_color, width=3)
    draw.polygon([(x1, y1), (x1 - 10, y1 - 5), (x1 - 10, y1 + 5)], fill=axis_color)
    draw.text((x1 + 5, y1 - font_size // 2), label_x, font=font, fill=axis_color)

    # Ось Y (вверх)
    x0 = offset
    y0 = h - offset
    x1 = x0
    y1 = y0 - arrow_len
    draw.line((x0, y0, x1, y1), fill=axis_color, width=3)
    draw.polygon([(x1, y1), (x1 - 5, y1 + 10), (x1 + 5, y1 + 10)], fill=axis_color)
    draw.text((x1 + 5, y1 - font_size), label_y, font=font, fill=axis_color)

    return img


def add_border(img: Image.Image,
               border_size: int | Tuple[int, int, int, int],
               fill: str | Tuple[int, int, int] = "black",
               rect_corner: str = "top-left",
               rect_size: Tuple[int, int] = (40, 40),
               rect_color: str = "black",
               label: Optional[str] = None,
               label_color: str = "white",
               font_size: int = 24) -> Image.Image:
    """
    Добавляет рамку, рисует прямоугольник в углу и размещает в нём текст (если задан).
    """
    if isinstance(border_size, int):
        border = (border_size, border_size, border_size, border_size)
    else:
        border = border_size

    img_with_border = ImageOps.expand(img, border=border, fill=fill)
    draw = ImageDraw.Draw(img_with_border)
    img_w, img_h = img_with_border.size
    rect_w, rect_h = rect_size

    left, top, right, bottom = border
    coords = {
        "top-left":     (left, top, left + rect_w, top + rect_h),
        "top-right":    (img_w - right - rect_w, top, img_w - right, top + rect_h),
        "bottom-left":  (left, img_h - bottom - rect_h, left + rect_w, img_h - bottom),
        "bottom-right": (img_w - right - rect_w, img_h - bottom - rect_h, img_w - right, img_h - bottom),
    }

    if rect_corner not in coords:
        raise ValueError("rect_corner должен быть одним из: top-left, top-right, bottom-left, bottom-right")

    rect = coords[rect_corner]
    draw.rectangle(rect, fill=rect_color)

    if label:
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()

        
        label = f"({label})"
        
        # Центр текста внутри прямоугольника
        bbox = draw.textbbox((0, 0), label, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        
        x0, y0, x1, y1 = rect
        center_x = x0 + (x1 - x0 - text_w) // 2
        center_y = y0 + (y1 - y0 - text_h) // 2
        draw.text((center_x, center_y), label, font=font, fill=label_color)

    return img_with_border
    
    
def add_label(img: Image.Image,
              label: str,
              position: Tuple[int, int] = (15, 15),
              font_size: int = 40,
              font_color: str = "black") -> Image.Image:
    """
    Добавляет подпись в изображение (внутри изображения).
    """
    img = img.copy()
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    draw.text(position, label, font=font, fill=font_color)
    return img
    
def load_images(folder: str | Path) -> List[Image.Image]:
    path = Path(folder)
    images = []
    
    for ext in ("*.png", "*.jpg", "*.jpeg"):
        images.extend([Image.open(p) for p in path.glob(ext)])

    return images


def compose_images(images: List[Image.Image],
                   layout: str = "row",
                   spacing: int = 10,
                   bg_color="white",
                   grid_cols: Optional[int] = None,
                   grid_rows: Optional[int] = None,
                   draw_axes: bool = False,
                   axis_labels: Tuple[str, str] = ("X", "Y")) -> Image.Image:
    
    if not images:
        raise ValueError("Список изображений пуст")

    images_original = images.copy()

    # Добавляем рамку ко всем изображениям
    mode = "cyrillic"  # или "latin", "arabic", "roman", "cyrillic"
    border = (10, 10, 10, 10)
    rect_corner = "top-left"
    rect_size = (100, 100)

    images = []
    for i, img in enumerate(images_original):
        img = add_border(
            img,
            border_size=border,
            rect_corner=rect_corner,
            rect_size=rect_size,
            rect_color="white",
            label=get_label(i, mode=mode),
            label_color="black",
            font_size=40
        )
        if draw_axes:
            img = add_axes(img, label_x=axis_labels[0], label_y=axis_labels[1])
        images.append(img)


    widths, heights = zip(*(img.size for img in images))

    if layout == "row":
        total_width = sum(widths) + spacing * (len(images) - 1)
        max_height = max(heights)
        result = Image.new("RGB", (total_width, max_height), color=bg_color)
        x = 0
        for img in images:
            result.paste(img, (x, 0))
            x += img.width + spacing

    elif layout == "column":
        max_width = max(widths)
        total_height = sum(heights) + spacing * (len(images) - 1)
        result = Image.new("RGB", (max_width, total_height), color=bg_color)
        y = 0
        for img in images:
            result.paste(img, (0, y))
            y += img.height + spacing

    elif layout == "grid":
        n = len(images)

        # Автоматическое определение сетки
        if grid_cols is None and grid_rows is None:
            grid_cols = math.ceil(math.sqrt(n))
            grid_rows = math.ceil(n / grid_cols)
        elif grid_cols is not None and grid_rows is None:
            grid_rows = math.ceil(n / grid_cols)
        elif grid_rows is not None and grid_cols is None:
            grid_cols = math.ceil(n / grid_rows)
        # Если заданы оба — используем как есть (даже если они > n)

        max_width = max(widths)
        max_height = max(heights)

        grid_width = grid_cols * max_width + (grid_cols - 1) * spacing
        grid_height = grid_rows * max_height + (grid_rows - 1) * spacing

        result = Image.new("RGB", (grid_width, grid_height), color=bg_color)

        for idx, img in enumerate(images):
            row = idx // grid_cols
            col = idx % grid_cols
            x = col * (max_width + spacing)
            y = row * (max_height + spacing)
            result.paste(img, (x, y))

    else:
        raise ValueError("layout должен быть 'row', 'column' или 'grid'")

    return result



images = load_images("./images")
grid_img = compose_images(
    images,
    layout="grid",
    spacing=50,
    draw_axes=True,
    axis_labels=("Step", "R")
)
grid_img.show()
grid_img.save("test.png")