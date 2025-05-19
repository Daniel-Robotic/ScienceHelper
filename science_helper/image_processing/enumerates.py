from enum import Enum


class LayoutMode(Enum):
    """Enumeration of available layout modes for image composition.

    Attributes:
        ROW (str): Arrange images horizontally in a single row.
        COLUMN (str): Arrange images vertically in a single column.
        GRID (str): Arrange images in a 2D grid.
    """

    ROW = "row"
    COLUMN = "column"
    GRID = "grid"


class SignaturePosition(Enum):
    """Enumeration of possible positions for signature labels on images.

    Attributes:
        TOP_LEFT (str): Place the label in the top-left corner.
        TOP_RIGHT (str): Place the label in the top-right corner.
        BOTTOM_LEFT (str): Place the label in the bottom-left corner.
        BOTTOM_RIGHT (str): Place the label in the bottom-right corner.
    """

    TOP_LEFT = "top-left"
    TOP_RIGHT = "top-right"
    BOTTOM_LEFT = "bottom-left"
    BOTTOM_RIGHT = "bottom-right"


class LabelMode(Enum):
    """Enumeration of supported label formats for image annotations.

    Attributes:
        LATIN_LOWER (str): Use lowercase Latin letters (a, b, c, ...).
        LATIN_UPPER (str): Use uppercase Latin letters (A, B, C, ...).
        CYRILLIC_LOWER (str): Use lowercase Cyrillic letters (а, б, в, ...).
        CYRILLIC_UPPER (str): Use uppercase Cyrillic letters (А, Б, В, ...).
        ARABIC (str): Use Arabic numerals (1, 2, 3, ...).
        ROMAN (str): Use Roman numerals (I, II, III, ...).
    """
    
    LATIN_LOWER = "latin_lower"
    LATIN_UPPER = "latin_upper"
    CYRILLIC_LOWER = "cyrillic_lower"
    CYRILLIC_UPPER = "cyrillic_upper"
    ARABIC = "arabic"
    ROMAN = "roman"
