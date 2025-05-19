from pathlib import Path

from PIL import Image

from science_helper.image_processing.enumerates import LabelMode, LayoutMode, SignaturePosition


def to_roman(n: int) -> str:
    """Convert an integer to its Roman numeral representation.

    Supports values from 1 and above, using standard Roman numeral symbols:
    M, D, C, L, X, V, and I. The algorithm performs a greedy decomposition
    using predefined value-symbol pairs.

    Args:
        n (int): The integer number to convert. Must be ≥ 1.

    Returns:
        str: The Roman numeral representation of the input number.

    Raises:
        ValueError: If `n` is less than 1.
    """
    val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syms = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
    roman = ""
    for i in range(len(val)):
        count = n // val[i]
        roman += syms[i] * count
        n -= val[i] * count
    return roman


def get_label(index: int, mode: str | LabelMode = LabelMode.CYRILLIC_LOWER) -> str:
    """Return a label string based on the specified mode and index.

    Supports multiple label modes including Latin, Cyrillic, Arabic numerals,
    and Roman numerals. The index defines the position in the corresponding label set.

    Args:
        index (int): The index of the label (starting from 0).
        mode (str | LabelMode, optional): The labeling mode to use.
            Can be a string or `LabelMode` enum. Defaults to `LabelMode.CYRILLIC_LOWER`.

    Returns:
        str: A label corresponding to the given index and mode.

    Raises:
        ValueError: If the index is out of range for Cyrillic modes (≥32).
        ValueError: If the provided mode is not recognized.

    Supported modes:
        - 'latin_lower' → 'a', 'b', ...
        - 'latin_upper' → 'A', 'B', ...
        - 'cyrillic_lower' → 'а', 'б', ...
        - 'cyrillic_upper' → 'А', 'Б', ...
        - 'arabic' → '1', '2', ...
        - 'roman' → 'I', 'II', ...
    """ 
    mode = mode.value if isinstance(mode, LabelMode) else mode

    match mode:
        case "latin_lower":
            return chr(ord("a") + index)
        case "latin_upper":
            return chr(ord("A") + index)
        case "cyrillic_lower" | "cyrillic_upper":
            base = ord("а") if mode == "cyrillic_lower" else ord("А")
            if index >= 32:  # noqa: PLR2004
                raise ValueError(f"The {index} index goes beyond the Cyrillic alphabet")
            return chr(base + index)
        case "arabic":
            return str(index + 1)
        case "roman":
            return to_roman(index + 1)
        case _:
            available = ", ".join(m.value for m in LabelMode)
            raise ValueError(f"Неверный режим: '{mode}'. Доступные режимы: {available}")


class ImageProcessing:
    """A class for processing, composing, and annotating a collection of images.

    This class provides functionality for:
    - Loading images from a folder
    - Drawing borders around images
    - Adding numbered labels or custom text
    - Drawing coordinate axes (X, Y)
    - Exporting the final composition as a single image

    Attributes:
        FONT_FAMILY_PATH (Path): Path to the directory containing available `.ttf` fonts.

    Examples:
        >>> processor = ImageProcessing(images_path="data/images", signature=True)
        >>> composed = processor()
        >>> composed.show()
    """

    FONT_FAMILY_PATH = Path("./scienceHelper/image_processing/fonts/")

    def __init__(  # noqa: PLR0913
        self,
        images_path: str | Path,
        border_size: int | tuple[int, int, int, int] | None = 10,
        border_fill: str | tuple[int, int, int] = "black",
        signature: bool = True,
        signature_label: str | tuple[str] | LabelMode | None = "latin_lower",
        signature_label_color: str = "white",
        signature_pos: str | SignaturePosition = "top-left",
        signature_size: tuple[int, int] = (40, 40),
        signature_color: str = "black",
        signature_font_size: int = 24,
        draw_axis: bool = False,
        axis_labels: tuple[str, str] | tuple[tuple[str], tuple[str]] = ("X", "Y"),
        axis_offset: int | tuple[int, int] = 20,
        axis_length: int = 60,
        axis_width: int = 3,
        axis_font_size: int = 24,
        font_family: str = "Arial",
    ):
        """Initialize the class for processing and composing images with optional borders, labels, and axis annotations.

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
        """  # noqa: E501
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
        """Return a human-readable string representation of the object."""
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
        """Return an unambiguous string representation of the object for debugging."""
        return (
            f"ImagesDesign(images_path={self.images_path!r}, "
            f"border_size={self.border_size!r}, border_fill={self.border_fill!r}, "
            f"signature={self.signature}, signature_label={self.signature_label!r}, "
            f"signature_label_color={self.signature_label_color!r}, "
            f"signature_pos={self.signature_pos!r}, signature_size={self.signature_size!r}, "
            f"signature_font_size={self._signature_font_size}, "
            f"signature_color={self.signature_color!r}, "
            f"draw_axis={self.draw_axis}, axis_labels={self.axis_labels!r}, "
            f"axis_offset={self.axis_offset}, axis_length={self.axis_length}, "
            f"axis_font_size={self._axis_font_size})"
            f""
        )

    def __len__(self) -> int:
        """Return the number of images in the collection."""
        return len(self._images)

    def __getitem__(self, index: int) -> Image.Image:
        """Return the image at the specified index.

        Args:
            index (int): Index of the image to retrieve.

        Returns:
            Image.Image: The image at the specified index.

        Raises:
            TypeError: If the index is not an integer.
        """
        if not isinstance(index, int):
            raise TypeError("The index must be an integer")
        return self._images[index]

    def __setitem__(self, index: int, value: Image.Image) -> None:
        """Set an image at the specified index in the internal list.

        Args:
            index (int): The index at which to set the image.
            value (Image.Image): The image to insert at the specified index.

        Raises:
            TypeError: If the index is not an integer or value is not a PIL.Image.Image.
            IndexError: If the index is out of bounds.
        """
        if not isinstance(index, int):
            raise TypeError("The index must be an integer")
        if not isinstance(value, Image.Image):
            raise TypeError("The value must be an instance of PIL.Image.Image")
        if not (0 <= index < len(self._images)):
            raise IndexError(f"Index {index} outside the range of the image list")

        self._images[index] = value

    def __delitem__(self, index: int) -> None:
        """Delete the image at the specified index from the internal list.

        Args:
            index (int): The index of the image to delete.

        Raises:
            TypeError: If the index is not an integer.
            IndexError: If the index is out of bounds.
        """
        if not isinstance(index, int):
            raise TypeError("The index must be an integer")
        if not (0 <= index < len(self._images)):
            raise IndexError(f"Index {index} outside the range of the image list")
        del self._images[index]

    def __contains__(self, item: Image.Image) -> bool:
        """Check whether the given image exists in the internal list.

        Args:
            item (Image.Image): The image to search for.

        Returns:
            bool: True if the image is found, False otherwise.

        Raises:
            TypeError: If the provided item is not an instance of PIL.Image.Image.
        """
        if not isinstance(item, Image.Image):
            raise TypeError("Verification is only possible for objects of the PIL.Image type.Image")
        return item in self._images

    def __iter__(self):
        """Return an iterator over the internal list of images.

        Returns:
            Iterator[Image.Image]: An iterator over the stored images.
        """
        return iter(self._images)

    def __call__(
        self,
        layout: str | LayoutMode = "row",
        spacing: int = 10,
        bg_color: str = "white",
        grid_cols: int | None = None,
        grid_rows: int | None = None,
    ) -> Image.Image:
        """Compose and return a single image from the internal collection.

        This method allows the object to be called like a function, delegating to `united_images`.

        Args:
            layout (str | LayoutMode, optional): Layout mode for arranging images ("row", "grid", etc.). Defaults to "row".
            spacing (int, optional): Spacing in pixels between images. Defaults to 10.
            bg_color (str, optional): Background color for the final image. Defaults to "white".
            grid_cols (int | None, optional): Number of columns in grid layout. Required for grid mode. Defaults to None.
            grid_rows (int | None, optional): Number of rows in grid layout. Required for grid mode. Defaults to None.

        Returns:
            Image.Image: The composed image containing all processed images.
        """  # noqa: E501
        return self.united_images(
            layout=layout,
            spacing=spacing,
            bg_color=bg_color,
            grid_cols=grid_cols,
            grid_rows=grid_rows,
        )

    # Validation and conversion
    @staticmethod
    def _validate_font_family(path: Path, font_family):
        font_files = sorted([f.stem for f in path.glob("*.ttf") if f.is_file()])

        if font_family in font_files:
            return font_family

        return "Arial"

    @staticmethod
    def _validate_path(path):
        if not isinstance(path, str | Path):
            raise TypeError("images_path must be a str or Path")
        return Path(path)

    @staticmethod
    def _validate_border_size(border_size):
        if isinstance(border_size, int):
            return (border_size,) * 4
        if isinstance(border_size, tuple | list) and len(border_size) == 4:  # noqa: PLR2004
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
        if isinstance(value, tuple) and len(value) == 2:  # noqa: PLR2004
            return value
        raise TypeError(f"{name} must be a tuple of length 2")

    @classmethod
    def from_images(cls, images: list[Image.Image], **kwargs):
        """Create an instance of the class from a list of images.

        This method allows creating an `ImageProcessing` object directly from
        a list of `PIL.Image.Image` instances without loading them from disk.

        Args:
            images (list[Image.Image]): A list of PIL images to initialize the object with.
            **kwargs: Additional keyword arguments forwarded to the class constructor.

        Returns:
            ImageProcessing: An initialized instance containing the provided images.
        """
        obj = cls(images_path=".", **kwargs)
        obj._images = images
        return obj

    # Properties with setters and getters
    @property
    def images_path(self):
        """Get the path to the directory containing the input images.

        Returns:
            Path: The folder path where images are stored.
        """
        return self._images_path

    @images_path.setter
    def images_path(self, value):
        self._images_path = self._validate_path(value)

    @property
    def border_size(self):
        """Get the border size applied to each image.

        Returns:
            Tuple[int, int, int, int]: The border size as (left, top, right, bottom).
        """
        return self._border_size

    @border_size.setter
    def border_size(self, value):
        self._border_size = self._validate_border_size(value)

    @property
    def border_fill(self):
        """Get the color of the image border.

        Returns:
            Union[str, Tuple[int, int, int]]: The border color as a string or RGB tuple.
        """
        return self._border_fill

    @border_fill.setter
    def border_fill(self, value):
        self._border_fill = self._validate_color(value)

    @property
    def signature(self):
        """Check whether signature labels are enabled.

        Returns:
            bool: True if labels are to be drawn on images.
        """
        return self._signature

    @signature.setter
    def signature(self, value):
        if not isinstance(value, bool):
            raise TypeError("signature must be a boolean")
        self._signature = value

    @property
    def signature_label(self):
        """Get the label format or custom labels for image annotations.

        Returns:
            Union[str, Tuple[str], LabelMode, None]: The labeling strategy or labels.
        """
        return self._signature_label

    @signature_label.setter
    def signature_label(self, value):
        if not (isinstance(value, str | tuple | LabelMode) or value is None):
            raise TypeError("signature_label must be str, tuple, LabelMode or None")
        self._signature_label = value

    @property
    def signature_label_color(self):
        """Get the text color used for signature labels.

        Returns:
            str: The label text color.
        """
        return self._signature_label_color

    @signature_label_color.setter
    def signature_label_color(self, value):
        self._signature_label_color = self._validate_color(value)

    @property
    def signature_pos(self):
        """Get the position where the label is drawn on the image.

        Returns:
            Union[str, SignaturePosition]: The label position (e.g., "top-left").
        """
        return self._signature_pos

    @signature_pos.setter
    def signature_pos(self, value):
        if not isinstance(value, SignaturePosition | str):
            raise TypeError("signature_pos must be a SignaturePosition or string")
        self._signature_pos = value

    @property
    def signature_size(self):
        """Get the dimensions of the signature label box.

        Returns:
            Tuple[int, int]: Width and height of the label box.
        """
        return self._signature_size

    @signature_size.setter
    def signature_size(self, value):
        self._signature_size = self._validate_tuple_pair(value, "signature_size")

    @property
    def signature_color(self):
        """Get the background color of the signature label box.

        Returns:
            Union[str, Tuple[int, int, int]]: The box background color.
        """
        return self._signature_color

    @signature_color.setter
    def signature_color(self, value):
        self._signature_color = self._validate_color(value)

    @property
    def draw_axis(self):
        """Check whether coordinate axes are drawn on each image.

        Returns:
            bool: True if axes are enabled.
        """
        return self._draw_axis

    @draw_axis.setter
    def draw_axis(self, value):
        if not isinstance(value, bool):
            raise TypeError("draw_axis must be a boolean")
        self._draw_axis = value

    @property
    def axis_labels(self):
        """Get labels for the X and Y axes.

        Returns:
            Union[Tuple[str, str], Tuple[Tuple[str], Tuple[str]]]: Axis label(s).
        """
        return self._axis_labels

    @axis_labels.setter
    def axis_labels(self, value):
        if isinstance(value, tuple) and len(value) == 2:  # noqa: PLR2004
            self._axis_labels = value
        else:
            raise TypeError("axis_labels must be a tuple of two strings or tuples")

    @property
    def axis_offset(self):
        """Get the offset from the image edge where axes begin.

        Returns:
            Union[int, Tuple[int, int]]: Axis origin offset.
        """
        return self._axis_offset

    @axis_offset.setter
    def axis_offset(self, value):
        if not isinstance(value, int | tuple):
            raise TypeError("axis_offset must be an integer")
        self._axis_offset = value

    @property
    def axis_length(self):
        """Get the length of the X and Y axes.

        Returns:
            int: The length of each axis in pixels.
        """
        return self._axis_length

    @axis_length.setter
    def axis_length(self, value):
        if not isinstance(value, int):
            raise TypeError("axis_length must be an integer")
        self._axis_length = value

    @property
    def axis_width(self):
        """Get the thickness of the axes.

        Returns:
            int: Line width in pixels.
        """
        return self._axis_width

    @axis_width.setter
    def axis_width(self, value):
        if not isinstance(value, int):
            raise TypeError("axis_width must be an integer")
        self._axis_width = value

    @property
    def signature_font_size(self):
        """Get the font size used for signature labels.

        Returns:
            int: Font size in points.
        """
        return self._signature_font_size

    @signature_font_size.setter
    def signature_font_size(self, value):
        if not isinstance(value, int):
            raise TypeError("signature_font_size must be an integer")
        self._signature_font_size = value

    @property
    def axis_font_size(self):
        """Get the font size used for axis labels.

        Returns:
            int: Font size in points.
        """
        return self._axis_font_size

    @axis_font_size.setter
    def axis_font_size(self, value):
        if not isinstance(value, int):
            raise TypeError("axis_font_size must be an integer")
        self._axis_font_size = value

    @property
    def font_family(self):
        """Get the font family used for rendering labels.

        Returns:
            str: Name of the font family (must match a .ttf file).
        """
        return self._font_family

    @font_family.setter
    def font_family(self, value):
        if not isinstance(value, str):
            raise TypeError("font_family must be a string")

        self._font_family = self._validate_font_family(self.FONT_FAMILY_PATH, value)

    # Assistant methods
    def _get_label(self, index):
        valid_modes = {m.value for m in LabelMode}

        label_mode = self._signature_label
        if isinstance(label_mode, str | LabelMode) and (
            getattr(label_mode, "value", label_mode) in valid_modes
        ):
            label = get_label(index, label_mode)
        elif isinstance(label_mode, tuple):
            if index >= len(label_mode):
                raise IndexError(
                    f"The signature for the index {index} was not found in the transmitted tuple"
                )
            label = label_mode[index]
        elif isinstance(label_mode, str):
            label = label_mode
        else:
            raise ValueError(f"Incorrect signature format: {label_mode}")

        return label

    def _get_positions(self, image_w: int, image_h: int) -> list | tuple:
        rect_w, rect_h = self._signature_size
        left, top, right, bottom = self._border_size
        positions = {
            "top-left": (left, top, left + rect_w, top + rect_h),
            "top-right": (image_w - right - rect_w, top, image_w - right, top + rect_h),
            "bottom-left": (left, image_h - bottom - rect_h, left + rect_w, image_h - bottom),
            "bottom-right": (
                image_w - right - rect_w,
                image_h - bottom - rect_h,
                image_w - right,
                image_h - bottom,
            ),
        }

        key = (
            self._signature_pos.value
            if isinstance(self._signature_pos, SignaturePosition)
            else self._signature_pos
        )
        rect_position = positions.get(key)

        if not rect_position:
            raise ValueError(
                "rect_corner должен быть одним из: top-left, top-right, bottom-left, bottom-right"
            )

        return rect_position

    def _load_images(self, folder) -> list[Image.Image]:
        """Load all image files from the specified folder with supported extensions.

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
        """  # noqa: E501
        folder = Path(folder)
        images = []
        for ext in ("*.png", "*.jpg", "*.jpeg"):
            images.extend([Image.open(p) for p in folder.glob(ext)])

        return images

    def _resize_proportional(
        self, img: Image.Image, width: int | None = None, height: int | None = None
    ) -> Image.Image:
        """Resize an image proportionally based on the specified width or height.

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
        """  # noqa: E501
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
        """Append a single image to the internal image list.

        Validates that the input is an instance of `PIL.Image.Image` before adding it
        to the internal list of images.

        Args:
            image (Image.Image): The image to be added.

        Raises:
            TypeError: If the provided object is not an instance of `PIL.Image.Image`.
        """
        if not isinstance(image, Image.Image):
            raise TypeError("The value must be an instance of PIL.Image.Image")
        self._images.append(image)

    def _draw_border(self):
        pass

    def _add_numbering(self):
        pass

    def _add_axes(self):
        pass

    def _layout_images(self):
        pass

    # The implementer method
    def preprocessing_image(self):
        """Preprocess a single image by applying configured transformations.

        This may include adding borders, labels, and axis annotations.
        Intended to be called internally for each image before composition.
        """
        pass

    def united_images(self):
        """Compose all loaded images into a single combined image.

        The composition respects layout, spacing, and visual options such as
        borders, labels, and axes. Configuration is taken from instance attributes.

        Returns:
            Image.Image: The final combined image.
        """
        pass
