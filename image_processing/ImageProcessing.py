from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Tuple, Union
from PIL import Image, ImageOps, ImageDraw, ImageFont

from image_processing.enumerates import *


def to_roman(n: int) -> str:
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


def get_label(index: int, mode: str | LabelMode = LabelMode.CYRILLIC_LOWER) -> str:
    mode = mode.value if isinstance(mode, LabelMode) else mode

    match mode:
        case "latin_lower": return chr(ord('a') + index)
        case "latin_upper": return chr(ord('A') + index)
        case "cyrillic_lower" | "cyrillic_upper":
            base = ord('а') if mode == "cyrillic_lower" else ord('А')
            if index >= 32:
                raise ValueError(f"Индекс {index} выходит за пределы кириллического алфавита")
            return chr(base + index)
        case "arabic": return str(index + 1)
        case "roman": return to_roman(index + 1)
        case _:
            available = ", ".join(m.value for m in LabelMode)
            raise ValueError(f"Неверный режим: '{mode}'. Доступные режимы: {available}")
        

class ImageProcessing(ABC):

    def __init__(self,
                 images_path: Union[str, Path],
                 border_size: Union[int, Tuple[int, int, int, int], None] = 10,
                 border_fill: Union[str, Tuple[int, int, int]] = "black",
                 signature: bool = True,
                 signature_label: Union[str, Tuple[str], LabelMode, None] = "latin_lower",
                 signature_label_color: str = "white",
                 signature_pos: Union[str, SignaturePosition] = "top-left",
                 signature_size: Tuple[int, int] = (40, 40),
                 signature_color: str = "black",
                 signature_font_size: int = 24,
                 draw_axis: bool = False,
                 axis_labels: Union[Tuple[str, str], Tuple[Tuple[str], Tuple[str]]] = ("X", "Y"),
                 axis_offset: Union[int, Tuple[int, int]] = 20,
                 axis_length: int = 60,
                 axis_width: int = 3,
                 axis_font_size: int = 24,
                 font_family: str = "Arial",
                 ):

        """
        Initialize the class for processing and composing images with optional
        borders, labels, and axis annotations.

        Args:
            images_path (Union[str, Path]): Path to the folder containing image files (PNG, JPG, JPEG).
            border_size (Union[int, Tuple[int, int, int, int], None], optional): 
                Border size around each image. Can be:
                - int: uniform border on all sides,
                - tuple: (left, top, right, bottom),
                - None: no border.
                Defaults to 10.
            border_fill (Union[str, Tuple[int, int, int]], optional): 
                Color of the border. Can be a string color name (e.g., "black") or an RGB tuple. Defaults to "black".
            signature (bool, optional): Whether to add a label/numbering on each image. Defaults to True.
            signature_label (Union[str, Tuple[str], LabelMode, None], optional): 
                Labeling mode. Can be:
                - str: mode name ("latin_lower", "roman", etc.),
                - tuple of strings: custom labels per image,
                - LabelMode enum,
                - None: no labels.
                Defaults to "latin_lower".
            signature_label_color (str, optional): Color of the label text. Defaults to "white".
            signature_pos (SignaturePosition, optional): Position of the label on the image (top-left, bottom-right, etc.). Defaults to SignaturePosition.TOP_LEFT.
            signature_size (Tuple[int, int], optional): Size of the label box (width, height). Defaults to (40, 40).
            signature_color (str, optional): Background color of the label box. Defaults to "black".
            signature_font_size (int, optional): Font size for labels annotations. Defaults to 24.
            draw_axis (bool, optional): Whether to draw X and Y axes on each image. Defaults to False.
            axis_labels (Union[Tuple[str, str], Tuple[Tuple[str], Tuple[str]]], optional): 
                Labels for X and Y axes. Can be:
                - Tuple of two strings: global labels,
                - Tuple of two tuples: per-image labels.
                Defaults to ("X", "Y").
            axis_offset (int, optional): Distance in pixels from the image edge to the axis origin. Defaults to 20.
            axis_length (int, optional): Length of the drawn axes in pixels. Defaults to 60.
            axis_font_size (int, optional): Font size for axis annotations. Defaults to 24.

        Raises:
            TypeError: If any of the arguments are of incorrect type.
            ValueError: If label or axis settings are out of bounds or improperly defined.
        """

        self._signature_font_size = signature_font_size
        self._axis_font_size = axis_font_size
        self._font_family = font_family

        self.signature = signature
        self.draw_axis = draw_axis
        self.images_path = images_path
        self.border_size = border_size
        self.border_fill = border_fill
        self.axis_labels = axis_labels
        self.axis_offset = axis_offset
        self.axis_length = axis_length
        self.axis_width = axis_width
        self.signature_pos = signature_pos
        self.signature_size = signature_size
        self.signature_color = signature_color
        self.signature_label = signature_label
        self.signature_label_color = signature_label_color

    # Magic methods
    def __str__(self) -> str:
        return (
                f"ImagesDesign(\n"
                f"  images_path={self.images_path},\n"
                f"  border_size={self.border_size}, border_fill={self.border_fill},\n"
                f"  signature={self.signature}, signature_label={self.signature_label},\n"
                f"  signature_pos={self.signature_pos}, signature_size={self.signature_size},\n"
                f"  signature_font_size={self._signature_font_size},\n"
                f"  draw_axis={self.draw_axis}, axis_labels={self.axis_labels},\n"
                f"  axis_offset={self.axis_offset}, axis_length={self.axis_length},\n"
                f"  axis_font_size={self._axis_font_size}\n"
                f")"
            )
    
    def __repr__(self) -> str:
        return (
            f"ImagesDesign(images_path={repr(self.images_path)}, "
            f"border_size={repr(self.border_size)}, border_fill={repr(self.border_fill)}, "
            f"signature={self.signature}, signature_label={repr(self.signature_label)}, "
            f"signature_label_color={repr(self.signature_label_color)}, "
            f"signature_pos={repr(self.signature_pos)}, signature_size={repr(self.signature_size)}, "
            f"signature_font_size={self._signature_font_size}, signature_color={repr(self.signature_color)}, "
            f"draw_axis={self.draw_axis}, axis_labels={repr(self.axis_labels)}, "
            f"axis_offset={self.axis_offset}, axis_length={self.axis_length}, axis_font_size={self._axis_font_size})"
            f""
        )


    def __len__(self) -> int:
        return len(self._images)

    def __getitem__(self, index: int) -> Image.Image:
        if not isinstance(index, int):
            raise TypeError("The index must be an integer")
        return self._images[index]
    
    def __setitem__(self, index: int, value: Image.Image) -> None:
        if not isinstance(index, int):
            raise TypeError("The index must be an integer")
        if not isinstance(value, Image.Image):
            raise TypeError("The value must be an instance of PIL.Image.Image")
        if not (0 <= index < len(self._images)):
            raise IndexError(f"Index {index} outside the range of the image list")
        
        self._images[index] = value

    def __delitem__(self, index: int) -> None:
        if not isinstance(index, int):
            raise TypeError("The index must be an integer")
        if not (0 <= index < len(self._images)):
            raise IndexError(f"Index {index} outside the range of the image list")
        del self._images[index]

    def __contains__(self, item: Image.Image) -> bool:
        if not isinstance(item, Image.Image):
            raise TypeError("Verification is only possible for objects of the PIL.Image type.Image")
        return item in self._images
    
    def __iter__(self):
        return iter(self._images)

    def __call__(self, 
                 layout: Union[str, LayoutMode] = "row",
                 spacing: int = 10,
                 bg_color: str = "white",
                 grid_cols: Optional[int] = None,
                 grid_rows: Optional[int] = None) -> Image.Image:
        
        return self.united_images(layout=layout,
                                  spacing=spacing,
                                  bg_color=bg_color,
                                  grid_cols=grid_cols,
                                  grid_rows=grid_rows)

    # Validation and conversion
    @staticmethod
    def _validate_path(path):
        if not isinstance(path, (str, Path)):
            raise TypeError("images_path must be a str or Path")
        return Path(path)

    @staticmethod
    def _validate_border_size(border_size):
        if isinstance(border_size, int):
            return (border_size,) * 4
        if isinstance(border_size, (tuple, list)) and len(border_size) == 4:
            return tuple(border_size)
        if border_size is None:
            return (0,) * 4
        raise TypeError("border_size must be int, tuple of 4 elements, or None")

    @staticmethod
    def _validate_color(color):
        if isinstance(color, str):
            return color
        if isinstance(color, tuple) and all(isinstance(c, int) for c in color):
            return color
        raise TypeError("Color must be a string or tuple of ints")

    @staticmethod
    def _validate_tuple_pair(value, name):
        if isinstance(value, tuple) and len(value) == 2:
            return value
        raise TypeError(f"{name} must be a tuple of length 2")

    @staticmethod
    def _validate_font_family(font_family):
        font_files = sorted([f.stem for f in Path("./fonts/").glob('*.ttf') if f.is_file()])

        if font_family in font_files:
            return font_family
        
        return "Arial"

    @classmethod
    def from_images(cls, images: List[Image.Image], **kwargs):
        obj = cls(images_path='.', **kwargs)
        obj._images = images
        return obj

    # Properties with setters and getters
    @property
    def images_path(self):
        return self._images_path

    @images_path.setter
    def images_path(self, value):
        self._images_path = self._validate_path(value)

    @property
    def border_size(self):
        return self._border_size

    @border_size.setter
    def border_size(self, value):
        self._border_size = self._validate_border_size(value)

    @property
    def border_fill(self):
        return self._border_fill

    @border_fill.setter
    def border_fill(self, value):
        self._border_fill = self._validate_color(value)

    @property
    def signature(self):
        return self._signature

    @signature.setter
    def signature(self, value):
        if not isinstance(value, bool):
            raise TypeError("signature must be a boolean")
        self._signature = value

    @property
    def signature_label(self):
        return self._signature_label

    @signature_label.setter
    def signature_label(self, value):
        if not (isinstance(value, (str, tuple, LabelMode)) or value is None):
            raise TypeError("signature_label must be str, tuple, LabelMode or None")
        self._signature_label = value

    @property
    def signature_label_color(self):
        return self._signature_label_color

    @signature_label_color.setter
    def signature_label_color(self, value):
        self._signature_label_color = self._validate_color(value)

    @property
    def signature_pos(self):
        return self._signature_pos

    @signature_pos.setter
    def signature_pos(self, value):
        if not isinstance(value, (SignaturePosition, str)):
            raise TypeError("signature_pos must be a SignaturePosition or string")
        self._signature_pos = value

    @property
    def signature_size(self):
        return self._signature_size

    @signature_size.setter
    def signature_size(self, value):
        self._signature_size = self._validate_tuple_pair(value, "signature_size")

    @property
    def signature_color(self):
        return self._signature_color

    @signature_color.setter
    def signature_color(self, value):
        self._signature_color = self._validate_color(value)

    @property
    def draw_axis(self):
        return self._draw_axis

    @draw_axis.setter
    def draw_axis(self, value):
        if not isinstance(value, bool):
            raise TypeError("draw_axis must be a boolean")
        self._draw_axis = value

    @property
    def axis_labels(self):
        return self._axis_labels

    @axis_labels.setter
    def axis_labels(self, value):
        if isinstance(value, tuple) and len(value) == 2:
            self._axis_labels = value
        else:
            raise TypeError("axis_labels must be a tuple of two strings or tuples")

    @property
    def axis_offset(self):
        return self._axis_offset

    @axis_offset.setter
    def axis_offset(self, value):
        if not isinstance(value, (int, tuple)):
            raise TypeError("axis_offset must be an integer")
        self._axis_offset = value

    @property
    def axis_length(self):
        return self._axis_length

    @axis_length.setter
    def axis_length(self, value):
        if not isinstance(value, int):
            raise TypeError("axis_length must be an integer")
        self._axis_length = value

    @property
    def axis_width(self):
        return self._axis_width

    @axis_width.setter
    def axis_width(self, value):
        if not isinstance(value, int):
            raise TypeError("axis_width must be an integer")
        self._axis_width = value

    @property
    def signature_font_size(self):
        return self._signature_font_size

    @signature_font_size.setter
    def signature_font_size(self, value):
        if not isinstance(value, int):
            raise TypeError("signature_font_size must be an integer")
        self._signature_font_size = value


    @property
    def axis_font_size(self):
        return self._axis_font_size

    @axis_font_size.setter
    def axis_font_size(self, value):
        if not isinstance(value, int):
            raise TypeError("axis_font_size must be an integer")
        self._axis_font_size = value

    @property
    def font_family(self):
        return self._font_family

    @font_family.setter
    def font_family(self, value):
        if not isinstance(value, str):
            raise TypeError("font_family must be a string")
        
        self._font_family = self._validate_font_family(value)

    # Assistant methods
    def _load_images(self, folder) -> List[Image.Image]:
        """
        Loads all image files from the specified folder with supported extensions.

        This method searches for files with `.png`, `.jpg`, and `.jpeg` extensions in the given folder,
        opens them using PIL, and returns a list of loaded images.

        Args:
            folder (Union[str, Path]): Path to the folder containing the images.

        Returns:
            List[PIL.Image.Image]: A list of loaded images.

        Notes:
            - Only files with extensions "*.png", "*.jpg", "*.jpeg" (case-sensitive) are loaded.
            - If the folder is empty or contains no supported image formats, an empty list is returned.
            - The input path is internally converted to `Path` using `pathlib`.

        Raises:
            FileNotFoundError: If the specified folder does not exist.
            PIL.UnidentifiedImageError: If an image file cannot be opened by PIL.
        """

        folder = Path(folder)
        images = []
        for ext in ("*.png", "*.jpg", "*.jpeg"):
            images.extend([Image.open(p) for p in folder.glob(ext)])
        
        return images
    
    def _resize_proportional(self, 
                             img: Image.Image, 
                             width: int = None, 
                             height: int = None) -> Image.Image:
        """
        Resize an image proportionally based on the specified width or height.

        This method adjusts the image size while preserving its aspect ratio
        if only `width` or `height` is provided. If both `width` and `height` are
        given, the image is resized exactly to that size (aspect ratio may be distorted).
        If neither is provided, the original image is returned unchanged.

        Args:
            img (PIL.Image.Image): The input image to be resized.
            width (int, optional): Target width. If specified alone, height will be adjusted proportionally.
            height (int, optional): Target height. If specified alone, width will be adjusted proportionally.

        Returns:
            PIL.Image.Image: A resized image according to the specified dimensions.
        """
        w, h = img.size

        if width and not height:
            ratio = width / w
            new_size = (width, int(h * ratio))
        elif height and not width:
            ratio = height / h
            new_size = (int(w * ratio), height)
        elif width and height:
            new_size = (width, height)
        else:
            return img

        return img.resize(new_size, Image.LANCZOS)

    def append(self, image: Image.Image):
        if not isinstance(image, Image.Image):
            raise TypeError("The value must be an instance of PIL.Image.Image")
        self._images.append(image)

    @abstractmethod
    def _draw_border(self): pass

    @abstractmethod
    def _add_numbering(self): pass

    @abstractmethod
    def _add_axes(self): pass
        
    @abstractmethod
    def _layout_images(self): pass

    # The implementer method
    @abstractmethod
    def preprocessing_image(self): pass
    
    @abstractmethod
    def united_images(self): pass

    
        