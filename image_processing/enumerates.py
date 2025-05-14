from enum import Enum


class PageSeries(Enum):
    A = "A"
    B = "B"
    C = "C"


class Orientation(Enum):
    PORTRAIT = 'portrait'
    LANDSCAPE = 'landscape'


class ColorMode(Enum):
    RGB = 'RGB'
    RGBA = 'RGBA'
    GRAY = 'L'
    

class LayoutMode(Enum):
    ROW = "row"
    COLUMN = "column"
    GRID = "grid"


class SignaturePosition(Enum):
    TOP_LEFT = "top-left"
    TOP_RIGHT = "top-right"
    BOTTOM_LEFT = "bottom-left"
    BOTTOM_RIGHT = "bottom-right"


class LabelMode(Enum):
    LATIN_LOWER = "latin_lower"
    LATIN_UPPER = "latin_upper"
    CYRILLIC_LOWER = "cyrillic_lower"
    CYRILLIC_UPPER = "cyrillic_upper"
    ARABIC = "arabic"
    ROMAN = "roman"