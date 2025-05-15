import math
from pathlib import Path
from typing import List, Optional, Tuple, Union
from PIL import Image, ImageOps, ImageDraw, ImageFont

from image_processing.enumerates import *
from image_processing.ImageProcessing import get_label, ImageProcessing
        

class ImagesDesign(ImageProcessing):

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

        super().__init__(images_path,
                        border_size,
                        border_fill,
                        signature,
                        signature_label,
                        signature_label_color,
                        signature_pos,
                        signature_size,
                        signature_color,
                        signature_font_size,
                        draw_axis,
                        axis_labels,
                        axis_offset,
                        axis_length,
                        axis_width,
                        axis_font_size,
                        font_family)

        self._load_fonts()
        self._images = self._load_images(self.images_path)


    # Assistant methods
    def _load_fonts(self):
        try:
            self._signature_font = ImageFont.truetype(f"./fonts/{self._font_family}.ttf", self._signature_font_size)
        except IOError:
            print("error")
            self._signature_font = ImageFont.load_default()

        try:
            self._axis_font = ImageFont.truetype(f"./fonts/{self._font_family}.ttf", self._axis_font_size)
        except IOError:
            self._axis_font = ImageFont.load_default()
    
    def _draw_border(self, image: Image.Image) -> Image.Image:
        """
        Adds a border around the given image using the configured border size and color.

        If the border size is non-zero, the image will be expanded using the specified padding and fill color.
        Otherwise, the original image is returned unmodified.

        Args:
            image (PIL.Image.Image): The input image to which the border will be applied.

        Returns:
            PIL.Image.Image: The image with the border applied, or the original image if the border size is zero.

        Notes:
            - Border size and color are taken from `self._border_size` and `self._border_fill`.
            - This method does not modify the original image but returns a new one.
        """

        if self._border_size:
            return ImageOps.expand(image, border=self._border_size, fill=self._border_fill)
        return image

    def _add_numbering(self, img: Image.Image, label: Optional[str]) -> Image.Image:
        """
        Draws a label (e.g. a number or letter) inside a colored rectangle on the image.

        The label is positioned inside a rectangle at one of the predefined corners of the image,
        with padding taken into account from the border size. The rectangle serves as a background
        for the label text.

        Args:
            img (PIL.Image.Image): Image to which the label will be added.
            label (Optional[str]): Text to display as a label. If None or empty, the image is returned unchanged.

        Returns:
            PIL.Image.Image: The modified image with the label drawn at the specified corner.

        Raises:
            ValueError: If `self._signature_pos` is not one of the supported positions:
                'top-left', 'top-right', 'bottom-left', 'bottom-right'.

        Notes:
            - Label position and size are defined by `self._signature_pos` and `self._signature_size`.
            - Rectangle background color: `self._signature_color`.
            - Font and text color are defined by `self._font` and `self._signature_label_color`.
            - The function modifies the image in-place and returns the same reference.
        """

        if not label:
            return img

        draw = ImageDraw.Draw(img)
        w, h = img.size
        rect_w, rect_h = self._signature_size
        left, top, right, bottom = self._border_size

        positions = {
            "top-left":     (left, top, left + rect_w, top + rect_h),
            "top-right":    (w - right - rect_w, top, w - right, top + rect_h),
            "bottom-left":  (left, h - bottom - rect_w, left + rect_w, h - bottom),
            "bottom-right": (w - right - rect_w, h - bottom - rect_h, w - right, h - bottom),
        }

        key = self._signature_pos.value if isinstance(self._signature_pos, SignaturePosition) else self._signature_pos
        rect = positions.get(key)

        if not rect:
            raise ValueError("rect_corner должен быть одним из: top-left, top-right, bottom-left, bottom-right")

        draw.rectangle(rect, fill=self._signature_color)

        text_w, text_h = draw.textbbox((0, 0), label, font=self._signature_font)[2:]
        x0, y0, x1, y1 = rect
        cx = x0 + (x1 - x0 - text_w) // 2
        cy = y0 + (y1 - y0 - text_h) // 2
        draw.text((cx, cy), label, font=self._signature_font, fill=self._signature_label_color)

        return img

    def _add_axes(self, img: Image.Image, label_x: str, label_y: str) -> Image.Image:
        """
        Draws coordinate axes (X and Y) with arrowheads and labels on the given image.

        This method draws two perpendicular axes:
        - X-axis: From left to right near the bottom edge.
        - Y-axis: From bottom to top near the left edge.
        Both axes originate from the same point (`offset` from bottom-left corner) and are drawn with fixed length and arrowheads.
        Labels are rendered near the end of each axis.

        Args:
            img (PIL.Image.Image): The input image on which the axes will be drawn.
            label_x (str): Label text for the X-axis.
            label_y (str): Label text for the Y-axis.

        Returns:
            PIL.Image.Image: A copy of the original image with drawn axes and labels.

        Notes:
            - The method uses `self.axis_font_size` and `self._font` to style the labels.
            - Axes are drawn in black with fixed dimensions (offset = 20, length = 60 pixels).
        """
        img = img.copy()
        draw = ImageDraw.Draw(img)
        w, h = img.size

        # Handle axis_offset as int or tuple
        offset_x, offset_y = (self.axis_offset, self.axis_offset) \
            if isinstance(self.axis_offset, int) else self.axis_offset

        arrow_length = self._axis_width * 2.5
        arrow_half =  self._axis_width * 1.2

        x0, y0 = offset_x, h - offset_y

        # X-axis
        end_x = x0 + self.axis_length - arrow_length
        draw.line((x0, y0, end_x, y0), fill="black", width= self._axis_width)
        draw.polygon([
            (end_x + arrow_length, y0),
            (end_x, y0 - arrow_half),
            (end_x, y0 + arrow_half)
        ], fill="black")
        draw.text((end_x + arrow_length + 5, y0 - self._axis_font_size // 2), label_x, font=self._axis_font, fill="black")

        # Y-axis
        end_y = y0 - self.axis_length + arrow_length
        draw.line((x0, y0, x0, end_y), fill="black", width= self._axis_width)
        draw.polygon([
            (x0, end_y - arrow_length),
            (x0 - arrow_half, end_y),
            (x0 + arrow_half, end_y)
        ], fill="black")
        draw.text((x0 + 5, end_y - arrow_length - self._axis_font_size), label_y, font=self._axis_font, fill="black")

        return img
    
    def _layout_images(self,
                       images: List[Image.Image],
                       layout: Union[str, LayoutMode],
                       spacing: int,
                       bg_color: str,
                       cols: Optional[int],
                       rows: Optional[int]) -> Image.Image:

        """
        Arrange a list of processed images into a single composite image using the specified layout mode.

        Supported layout modes:
        - "row": Arrange images in a single horizontal row.
        - "column": Arrange images in a single vertical column.
        - "grid": Arrange images in a rectangular grid; the number of columns and/or rows can be specified or auto-calculated.

        Args:
            images (List[PIL.Image.Image]): List of images to arrange.
            layout (Union[str, LayoutMode]): Layout mode to use ("row", "column", or "grid").
            spacing (int): Number of pixels between images.
            bg_color (str): Background color for the canvas (e.g., "white", "black", or RGB tuple).
            cols (Optional[int]): Number of columns for grid layout. If None, calculated automatically.
            rows (Optional[int]): Number of rows for grid layout. If None, calculated automatically.

        Returns:
            PIL.Image.Image: A single composed image with the given layout and spacing.

        Raises:
            ValueError: If `layout` is not one of the supported values ("row", "column", "grid").
        """

        w_list, h_list = zip(*(img.size for img in images))
        layout = layout.value if isinstance(layout, LayoutMode) else layout

        if layout == "row":
            total_width = sum(w_list) + spacing * (len(images) - 1)
            max_height = max(h_list)
            canvas = Image.new("RGB", (total_width, max_height), color=bg_color)
            x = 0
            for img in images:
                canvas.paste(img, (x, 0))
                x += img.width + spacing
            return canvas

        if layout == "column":
            max_width = max(w_list)
            total_height = sum(h_list) + spacing * (len(images) - 1)
            canvas = Image.new("RGB", (max_width, total_height), color=bg_color)
            y = 0
            for img in images:
                canvas.paste(img, (0, y))
                y += img.height + spacing
            return canvas

        if layout == "grid":
            n = len(images)
            if cols is None and rows is None:
                cols = math.ceil(math.sqrt(n))
                rows = math.ceil(n / cols)
            elif cols is None:
                cols = math.ceil(n / rows)
            elif rows is None:
                rows = math.ceil(n / cols)

            max_w = max(w_list)
            max_h = max(h_list)
            canvas = Image.new("RGB", (
                cols * max_w + spacing * (cols - 1),
                rows * max_h + spacing * (rows - 1)
            ), color=bg_color)

            for idx, img in enumerate(images):
                row, col = divmod(idx, cols)
                x = col * (max_w + spacing)
                y = row * (max_h + spacing)
                canvas.paste(img, (x, y))
            return canvas

        raise ValueError("layout должен быть 'row', 'column' или 'grid'")

    # The implementer method
    def preprocessing_image(self,
                            index: int,
                            width: int = None, 
                            height: int = None) -> Image.Image:
        """
        Process a single image by optional resizing, adding a border, label, and axes.

        This method applies the following transformations to an image at the specified index:
        1. Resizes the image proportionally if `width` or `height` is provided.
        2. Adds a border using `_draw_border`.
        3. Adds a label (signature) if enabled and defined.
        4. Draws X and Y axes if enabled.

        Args:
            index (int): Index of the image in the internal image list.
            width (int, optional): Target width for resizing. Height is scaled proportionally if only width is provided.
            height (int, optional): Target height for resizing. Width is scaled proportionally if only height is provided.

        Returns:
            PIL.Image.Image: The processed image.

        Raises:
            IndexError: If the index is outside the bounds of the image list or a label index is out of range.
            ValueError: If the signature label is in an unsupported format.
        """

        if index >= len(self._images):
            raise IndexError(f"Index {index} outside the range of the image list")

        self._load_fonts()
        valid_modes = {m.value for m in LabelMode}
        img = self._images[index]
        if width and height:
            img = self._resize_proportional(img=img, width=width, height=height)
        proc = self._draw_border(img)

        if self._signature and self._signature_label:
            label_mode = self._signature_label
            if isinstance(label_mode, (str, LabelMode)) and (getattr(label_mode, 'value', label_mode) in valid_modes):
                label = get_label(index, label_mode)
            elif isinstance(label_mode, tuple):
                if index >= len(label_mode):
                    raise IndexError(f"The signature for the index {index} was not found in the transmitted tuple")
                label = label_mode[index]
            elif isinstance(label_mode, str):
                label = label_mode
            else:
                raise ValueError(f"Incorrect signature format: {label_mode}")
            proc = self._add_numbering(proc, label)

        if self._draw_axis:
            label_x, label_y = self._axis_labels
            if isinstance(label_x, tuple):
                lx, ly = label_x[index], label_y[index]
            else:
                lx, ly = label_x, label_y
            proc = self._add_axes(proc, lx, ly)

        return proc

    
    def united_images(self,
                      layout: Union[str, LayoutMode] = "row",
                      spacing: int = 10,
                      bg_color: str = "white",
                      grid_cols: Optional[int] = None,
                      grid_rows: Optional[int] = None,
                      width: int = None, 
                      height: int = None) -> Image.Image:

        """
        Compose and return a single image from a collection of images with optional borders, labels, and axes.

        The method applies the following operations to each image (in order):
        1. Adds a border if specified.
        2. Adds a signature/label if `signature=True`.
        3. Draws X and Y axes if `draw_axis=True`.
        Finally, the processed images are arranged into a single image using the selected layout.

        Args:
            layout (Union[str, LayoutMode], optional): 
                Layout mode for arranging images. Can be:
                - "row": images in a single horizontal row,
                - "column": images in a vertical column,
                - "grid": images in a rectangular grid.
                Defaults to "row".
            spacing (int, optional): Spacing in pixels between images. Defaults to 10.
            bg_color (str, optional): Background color of the resulting canvas. Defaults to "white".
            grid_cols (Optional[int], optional): Number of columns in the grid layout. Required if `layout="grid"` and number of rows is not given.
            grid_rows (Optional[int], optional): Number of rows in the grid layout. Required if `layout="grid"` and number of columns is not given.

        Returns:
            PIL.Image.Image: A single composed image with all processed individual images arranged according to the layout.

        Raises:
            ValueError: 
                - If the list of images is empty.
                - If `layout` is not one of "row", "column", "grid".
                - If label index is out of range for a provided tuple.
            TypeError: 
                - If label or axis configuration is of unsupported type.
        """

        if not self._images:
            raise ValueError("The list of images is empty")

        images = []
        for i in range(len(self._images)):
            proc = self.preprocessing_image(i, width=width, height=height)
            images.append(proc)

        return self._layout_images(images, layout, spacing, bg_color, grid_cols, grid_rows)
    
    
        