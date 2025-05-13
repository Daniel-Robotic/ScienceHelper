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