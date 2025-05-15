from enum import Enum


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