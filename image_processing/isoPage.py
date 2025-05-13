import math
from PIL import Image, ImageOps
from pathlib import Path
from typing import List, Optional
from image_processing.enumerates import * 


class ISOPage:
    
    BASE_SIZE_MM = {
        "A": (841, 1189),
        "B": (1000, 1414),
        "C": (917, 1297)
    }
    
    def __init__(self,
                 series: PageSeries = PageSeries.A,
                 number: int = 4,
                 dpi: int = 300,
                 orientation: Orientation = Orientation.PORTRAIT,
                 color_mode: ColorMode = ColorMode.RGB):
        
        self._series = series
        self._number = number
        self._dpi = dpi
        self._orientation = orientation
        self._color_mode = color_mode
        
        self._validate()
        
        width_mm, height_mm = self._calculate_size_mm()
        self._width_px = self._mm_to_px(width_mm)
        self._height_px = self._mm_to_px(height_mm)
        
        
        
    def _validate(self):
        if self._series.value not in self.BASE_SIZE_MM:
            raise ValueError("Допустимые серии: A, B, C")
        if not (0 <= self._number <= 10):
            raise ValueError("Номер должен быть от 0 до 10")
        
    def _calculate_size_mm(self) -> tuple[float, float]:
        base_w, base_h = self.BASE_SIZE_MM[self._series.value]
        
        if self._number % 2 == 0:
            w = base_w / (2 ** (self._number // 2))
            h = base_h / (2 ** (self._number // 2))
        else:
            w = base_w / (2 ** ((self._number + 1) // 2))
            h = base_h / (2 ** ((self._number + 1) // 2))
            
        if self._orientation == Orientation.LANDSCAPE:
            return max(w, h), min(w, h)
        
        return min(w, h), max(w, h)
    
    def _mm_to_px(self, mm: float) -> int:
        return int(mm / 25.4 * self._dpi)

    def create_image(self, color: str = "white") -> Image.Image:
        size = (self._width_px, self._height_px)
        img = Image.new(self._color_mode.value, size, color)
        img.info["dpi"] = (self._dpi, self._dpi)
        
        return img
    
    def save(self, path: str, color: str = "white"):
        img = self.create_image(color)
        img.save(path)
        
        
    def place_images(
        self,
        image_paths: List[Path],
        layout: LayoutMode,
        spacing: int = 10,
        margin: int = 100,
        grid_cols: Optional[int] = None,
        grid_rows: Optional[int] = None
    ) -> Image.Image:
        
        base = self.create_image()
        images = [Image.open(str(p)).convert(self._color_mode.value) for p in image_paths]
        count = len(images)

        # Внутреннее поле страницы
        content_x = margin
        content_y = margin
        content_w = self._width_px - 2 * margin
        content_h = self._height_px - 2 * margin

        if layout == LayoutMode.ROW:
            cell_w = (content_w - spacing * (count - 1)) // count
            cell_h = content_h
            for i, img in enumerate(images):
                thumb = ImageOps.contain(img, (cell_w, cell_h), Image.LANCZOS)
                offset_x = content_x + i * (cell_w + spacing) + (cell_w - thumb.width) // 2
                offset_y = content_y + (cell_h - thumb.height) // 2
                base.paste(thumb, (offset_x, offset_y))

        elif layout == LayoutMode.COLUMN:
            cell_h = (content_h - spacing * (count - 1)) // count
            cell_w = content_w
            for i, img in enumerate(images):
                thumb = ImageOps.contain(img, (cell_w, cell_h), Image.LANCZOS)
                offset_x = content_x + (cell_w - thumb.width) // 2
                offset_y = content_y + i * (cell_h + spacing) + (cell_h - thumb.height) // 2
                base.paste(thumb, (offset_x, offset_y))

        elif layout == LayoutMode.GRID:
            cols = grid_cols or math.ceil(math.sqrt(count))
            rows = grid_rows or math.ceil(count / cols)

            if grid_cols and not grid_rows:
                rows = math.ceil(count / cols)
            if grid_rows and not grid_cols:
                cols = math.ceil(count / rows)

            cell_w = (content_w - (cols - 1) * spacing) // cols
            cell_h = (content_h - (rows - 1) * spacing) // rows

            for i, img in enumerate(images):
                row = i // cols
                col = i % cols
                thumb = ImageOps.contain(img, (cell_w, cell_h), Image.LANCZOS)
                offset_x = content_x + col * (cell_w + spacing) + (cell_w - thumb.width) // 2
                offset_y = content_y + row * (cell_h + spacing) + (cell_h - thumb.height) // 2
                base.paste(thumb, (offset_x, offset_y))

        return base