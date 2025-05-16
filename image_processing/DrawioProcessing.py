import io 
import uuid
import base64
import xml.etree.ElementTree as ET

from PIL import Image
from pathlib import Path
from typing import Optional, Union
from image_processing.enumerates import *
from image_processing.ImageProcessing import ImageProcessing


class DrawioImageDesign(ImageProcessing):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._images = self._load_images(self._images_path)

        self._root = None 
        self._xml_root = None
        self._create_drawio_structure()

    # Методы родительского класса
    def _draw_border(self):
        """
        Generates a style string for the image border in draw.io format.

        Returns:
            str: A style string that defines the border color and stroke width 
                based on the object's `_border_fill` and the maximum of `_border_size`.
                Example: "imageBorder=#000;strokeWidth=10;"

        Used in:
            - Setting the border style for mxCell elements representing images.
        """
        return f"imageBorder={self._border_fill};strokeWidth={max(self._border_size)};"

    def _add_numbering(self,
                       image_w: int,
                       image_h: int,
                       label: str = "",
                       parent_id: str = "1"):
        
        """
        Adds a numbering label (e.g., index or identifier) to an image element 
        as an `mxCell` with geometry and styling for draw.io.

        Args:
            image_w (int): Width of the image in pixels.
            image_h (int): Height of the image in pixels.
            label (str, optional): The text label to display (e.g., a number or letter). Defaults to "".
            parent_id (str, optional): The ID of the parent `mxCell` group or image. Defaults to "1".

        Behavior:
            - Computes a position for the label based on `_signature_pos` (e.g., top-right).
            - Applies an offset using `_border_size`.
            - Creates a styled `mxCell` for the label and positions it using `mxGeometry`.

        Used in:
            - `preprocessing_image()` for attaching index/label annotations to image blocks.
        """

        x0, y0, _, _ = self._get_positions(image_w, image_h)
        offset = max(self._border_size)
        key = self._signature_pos.value if isinstance(self._signature_pos, SignaturePosition) else self._signature_pos

        pos_map = {
            SignaturePosition.TOP_LEFT.value: (-offset, -offset),
            SignaturePosition.TOP_RIGHT.value: (offset, -offset),
            SignaturePosition.BOTTOM_LEFT.value: (-offset, offset),
            SignaturePosition.BOTTOM_RIGHT.value: (offset, offset)
        }

        dx, dy = pos_map.get(key, (0, 0))
        x0 += dx
        y0 += dy
        
        cell = self._create_mx_cell(
            id=self._generate_id(suffix="-numbering"),
            value=self._get_numbering_text(label),
            style=self._get_numbering_style(),
            vertex="1",
            parent=parent_id
        )

        self._create_mx_geometry(
            cell,
            x=str(x0),
            y=str(y0),
            width=str(self._signature_size[0]),
            height=str(self._signature_size[1])
        )
        

    def _add_axes(self,
              image_w: int,
              image_h: int,
              label_x: str,
              label_y: str,
              parent_id: str = "1"):

        """
        Adds X and Y axes with corresponding labels to an image element.

        Args:
            image_w (int): Width of the image in pixels.
            image_h (int): Height of the image in pixels.
            label_x (str): Text label for the X axis.
            label_y (str): Text label for the Y axis.
            parent_id (str, optional): The ID of the parent `mxCell` group (usually the image). Defaults to "1".

        Behavior:
            - Calculates the total size required to draw the axes including labels.
            - Creates a group `mxCell` to contain the axes.
            - Draws two axis lines using `_create_axis`:
                - X axis: horizontal line from (0, height) to (axis_length, height)
                - Y axis: vertical line from (0, height) to (0, height - axis_length)
            - Adds text labels near the ends of each axis using `_add_label`.

        Used in:
            - `preprocessing_image()` when axis display is enabled (`_draw_axis=True`).
        """

        offset_x, offset_y = (self._axis_offset, self._axis_offset) if isinstance(self._axis_offset, int) else self._axis_offset

        label_x_width = len(label_x) * self._axis_font_size * 0.6
        label_y_height = len(label_y) * self._axis_font_size * 0.6

        width = self._axis_length + 5 + label_x_width
        height = self._axis_length + 5 + label_y_height

        group_id = self._generate_id(suffix="-axisgroup")
        style = self._get_text_style()

        group_cell = self._create_mx_cell(
            id=group_id,
            value="",
            style="group",
            vertex="1",
            connectable="0",
            parent=parent_id
        )
        self._create_mx_geometry(
            group_cell,
            x=str(offset_x),
            y=str(image_h - offset_y - height),
            width=str(width),
            height=str(height)
        )

        x0, y0 = 0, height
        x_end = self._axis_length
        y_end = height - self._axis_length

        xaxis_id = self._generate_id(suffix="-xaxis")
        yaxis_id = self._generate_id(suffix="-yaxis")
        xlabel_id = self._generate_id(suffix="-xlabel")
        ylabel_id = self._generate_id(suffix="-ylabel")

        self._create_axis(xaxis_id, x0, y0, x_end, y0, group_id)
        self._create_axis(yaxis_id, x0, y0, x0, y_end, group_id)

        self._add_label(xlabel_id, label_x, x_end + 5, y0 - 10, len(label_x), group_id, style)
        self._add_label(ylabel_id, label_y, x0 + 5, y_end - self._axis_font_size, len(label_y), group_id, style)
        
    def _layout_images(self,
                       layout: str = "row",
                       spacing: int = 10,
                       grid_cols: Optional[int] = None,
                       grid_rows: Optional[int] = None):
        """
        Arranges multiple images in a specified layout (row, column, or grid)
        and groups them into a single parent mxCell in the draw.io structure.

        Args:
            layout (str, optional): Layout mode: "row", "column", or "grid". Defaults to "row".
            spacing (int, optional): Spacing in pixels between images. Defaults to 10.
            grid_cols (Optional[int], optional): Number of columns in grid layout. Used only if layout is "grid".
            grid_rows (Optional[int], optional): Number of rows in grid layout. Used only if layout is "grid".

        Behavior:
            - Calculates (x, y) positions for each image depending on layout type:
                - "row": horizontally aligned images.
                - "column": vertically stacked images.
                - "grid": images arranged in a 2D grid.
            - Calls `preprocessing_image()` for each image with its computed position.
            - Wraps all images in a group `mxCell` with geometry sized to fit all children.

        Raises:
            ValueError: If an unsupported layout type is provided.

        Used in:
            - `united_images()` to render the full composed diagram from the image list.
        """
        image_w, image_h = self._images[0].size
        positions = []

        if layout == LayoutMode.ROW.value:
            for i in range(len(self._images)):
                x = i * (image_w + spacing)
                y = 0
                positions.append((x, y))

        elif layout == LayoutMode.COLUMN.value:
            for i in range(len(self._images)):
                x = 0
                y = i * (image_h + spacing)
                positions.append((x, y))
        elif layout == LayoutMode.GRID.value:
            n = len(self._images)
            cols = grid_cols or int(n ** 0.5)
            rows = grid_rows or ((n + cols - 1) // cols)
            for idx in range(n):
                col = idx % cols
                row = idx // cols
                x = col * (image_w + spacing)
                y = row * (image_h + spacing)
                positions.append((x, y))
        else:
            raise ValueError(f"Unknown layout type: {layout}")
        

        group_id = self._generate_id(suffix="-group")

        group_cell = self._create_mx_cell(
            id=group_id,
            value="",
            style="group",
            vertex="1",
            connectable="0",
            parent="1"
        )

        
        all_right = []
        all_bottom = []
        for i, (x, y) in enumerate(positions):
            self.preprocessing_image(index=i, 
                                     position_x=x, 
                                     position_y=y,
                                     parent_id=group_id)
            all_right.append(x + image_w)
            all_bottom.append(y + image_h)
            
        self._create_mx_geometry(
            group_cell,
            x="30",
            y="30",
            width=str(max(all_right)),
            height=str(max(all_bottom))
        )
        

    def preprocessing_image(self,
                            index: int,
                            width: int | None = None,
                            height: int | None = None,
                            position_x: int = 0,
                            position_y: int = 0,
                            parent_id: str = "1"):
        """
        Processes a single image from the internal image list by resizing,
        encoding, and embedding it into the draw.io diagram as an `mxCell`.

        Args:
            index (int): Index of the image in the `_images` list.
            width (int | None, optional): Target width for resizing. If None, original width is preserved.
            height (int | None, optional): Target height for resizing. If None, original height is preserved.
            position_x (int, optional): X-coordinate of the image within the parent container. Defaults to 0.
            position_y (int, optional): Y-coordinate of the image within the parent container. Defaults to 0.
            parent_id (str, optional): ID of the parent `mxCell` group. Defaults to "1".

        Behavior:
            - Resizes the image proportionally if dimensions are provided.
            - Converts the image to base64 and embeds it into a styled `mxCell`.
            - Adds geometry based on specified position and image size.
            - Optionally adds:
                - A numbering label (`_add_numbering`) if `_signature` and `_signature_label` are enabled.
                - Coordinate axes (`_add_axes`) if `_draw_axis` is enabled.

        Raises:
            IndexError: If the provided index is out of bounds.

        Used in:
            - `_layout_images()` and other high-level composition methods.
        """
        if index >= len(self._images):
            raise IndexError(f"Index {index} outside the range of the image list")

        image = self._resize_proportional(self._images[index], width, height)
        image_w, image_h = image.size

        image_base64 = self._image_to_base64(image)
        cell_id = self._generate_id(suffix=f"-{index+1}")

        style = ("shape=image;",
                 "verticalLabelPosition=bottom;",
                 "labelBackgroundColor=default;",
                 "verticalAlign=top;",
                 "aspect=fixed;",
                 "imageAspect=0;",
                 f"image=data:image/png,{image_base64};",
                 self._draw_border()
                )

        cell = self._create_mx_cell(
            id=cell_id,
            value="",
            style="".join(style),
            vertex="1",
            parent=parent_id
        )

        self._create_mx_geometry(
            cell,
            x=str(position_x),
            y=str(position_y),
            width=str(image_w),
            height=str(image_h)
        )

        if self._signature and self._signature_label:
            self._add_numbering(image_w=image_w, image_h=image_h, 
                                label=self._get_label(index=index), 
                                parent_id=cell_id)

        if self._draw_axis:
            lx, ly = self._axis_labels
            lx, ly = (lx[index], ly[index]) if isinstance(lx, tuple) else (lx, ly)
            self._add_axes(image_w, image_h, label_x=lx, label_y=ly, parent_id=cell_id)


    def united_images(self,
                      layout: Union[str, LayoutMode] = "row",
                      spacing: int = 10,
                      grid_cols: Optional[int] = None,
                      grid_rows: Optional[int] = None,
                      width: int = None,
                      height: int = None):
        """
        Composes all loaded images into a single layout group and generates 
        the corresponding draw.io structure.

        Args:
            layout (Union[str, LayoutMode], optional): Layout mode for arranging images.
                Can be "row", "column", or "grid". Defaults to "row".
            spacing (int, optional): Spacing between images in pixels. Defaults to 10.
            grid_cols (Optional[int], optional): Number of columns in grid layout. Only used if layout is "grid".
            grid_rows (Optional[int], optional): Number of rows in grid layout. Only used if layout is "grid".
            width (int, optional): If set, resizes all images to this width before layout.
            height (int, optional): If set, resizes all images to this height before layout.

        Behavior:
            - Optionally resizes all images to the specified `width` and `height`.
            - Passes control to `_layout_images()` to arrange the images based on the selected layout mode.

        Used in:
            - `export_to_drawio()` to generate the final diagram for export.
        """
        layout = layout.value if isinstance(layout, LayoutMode) else layout
        
        if width or height:
            self._images = [self._resize_proportional(img, width=width, height=height) for img in self._images]
         
        self._layout_images(layout=layout,
                            spacing=spacing,
                            grid_cols=grid_cols,
                            grid_rows=grid_rows)

    # методы этого класса
    def _create_drawio_structure(self):
        """
        Initializes the root XML structure for a draw.io diagram.

        Behavior:
            - Creates the top-level <mxfile> element with the draw.io host attribute.
            - Adds a <diagram> element with a unique ID and a predefined name ("Обработчик изображений").
            - Constructs the <mxGraphModel> and its <root> container.
            - Adds two base `mxCell` elements with IDs "0" and "1", where:
                - ID "0" is the invisible root of all elements.
                - ID "1" serves as the main container for the user-defined content.

        Used in:
            - Constructor (`__init__`) to prepare an empty draw.io-compatible structure.
            - Required before adding any cells, images, or layout groups.
        """
        self._root = ET.Element("mxfile", host="ScienceHelper")
        
        diagram_id = self._generate_id(prefix="", suffix="")
        diagram = ET.SubElement(self._root, "diagram", 
                                name="Обработчик изображений", 
                                id=diagram_id)
        
        model = ET.SubElement(diagram, "mxGraphModel")
        self._xml_root = ET.SubElement(model, "root")

        ET.SubElement(self._xml_root, "mxCell", id="0")
        ET.SubElement(self._xml_root, "mxCell", id="1", parent="0")

    def _create_mx_cell(self, **attrs) -> ET.Element:
        """
        Creates and appends an <mxCell> element to the draw.io XML structure.

        Args:
            **attrs: Arbitrary keyword arguments representing XML attributes
                    for the <mxCell> element (e.g., id, value, style, parent, vertex, edge).

        Returns:
            ET.Element: The newly created <mxCell> element.

        Behavior:
            - Appends the element to the internal `_xml_root` container.

        Used in:
            - Most rendering methods to define images, groups, arrows, and text labels.
        """
        return ET.SubElement(self._xml_root, "mxCell", **attrs)
    
    def _create_mx_geometry(self, parent: ET.Element, **attrs) -> ET.Element:
        """
        Creates and appends an <mxGeometry> element to a given <mxCell> element.

        Args:
            parent (ET.Element): The parent <mxCell> element to which the geometry is attached.
            **attrs: Arbitrary keyword arguments representing attributes of the <mxGeometry> element
                    (e.g., x, y, width, height, relative).

        Returns:
            ET.Element: The newly created <mxGeometry> element.

        Behavior:
            - Sets the "as" attribute to "geometry", indicating its role in the draw.io structure.
            - Used to define the position and size of an <mxCell>.

        Used in:
            - Image blocks, labels, axes, and other visual elements requiring placement.
        """
        geom = ET.SubElement(parent, "mxGeometry", **attrs)
        geom.set("as", "geometry")
        return geom

    def _create_axis(self, 
                     id: str, 
                     x0: float, 
                     y0: float, 
                     x1: float, 
                     y1: float, 
                     parent_id: str):
        """
        Creates a visual axis (as an edge with an arrow) and appends it to the draw.io XML structure.

        Args:
            id (str): Unique ID for the axis mxCell.
            x0 (float): X-coordinate of the axis starting point.
            y0 (float): Y-coordinate of the axis starting point.
            x1 (float): X-coordinate of the axis ending point.
            y1 (float): Y-coordinate of the axis ending point.
            parent_id (str): ID of the parent mxCell group.

        Behavior:
            - Creates an edge-style `mxCell` with a thin arrowhead and custom stroke width.
            - Adds an `mxGeometry` block with relative positioning.
            - Defines `mxPoint` elements for the source and target coordinates of the axis line.

        Used in:
            - `_add_axes()` to render X and Y directional lines next to images.
        """
        cell = self._create_mx_cell(
            id=id,
            value="",
            style=f"endArrow=blockThin;html=1;rounded=0;strokeWidth={self._axis_width}",
            edge="1",
            parent=parent_id
        )

        geom = self._create_mx_geometry(cell, width="50", height="50", relative="1")

        source = ET.SubElement(geom, "mxPoint", x=str(x0), y=str(y0))
        target = ET.SubElement(geom, "mxPoint", x=str(x1), y=str(y1))

        source.set("as", "sourcePoint")
        target.set("as", "targetPoint")

    def _add_label(self, 
                   cell_id: str, 
                   text: str, 
                   x: float, 
                   y: float, 
                   width: int, 
                   parent_id: str, 
                   style: str):
        """
        Adds a text label as an `mxCell` element to the draw.io diagram.

        Args:
            cell_id (str): Unique ID for the label mxCell.
            text (str): The text content to display.
            x (float): X-coordinate of the label position.
            y (float): Y-coordinate of the label position.
            width (int): Logical width of the text (multiplied by font size to determine pixel width).
            parent_id (str): ID of the parent mxCell (e.g., an axis group).
            style (str): The style string for the label (e.g., font, color, alignment).

        Behavior:
            - Creates a vertex `mxCell` containing the label text.
            - Applies style and attaches it to the given parent cell.
            - Defines the geometry (position and size) based on coordinates and scaled text width.

        Used in:
            - `_add_axes()` for axis labels.
            - Any other diagram element that needs textual annotation.
        """
        
        cell = self._create_mx_cell(
            id=cell_id, value=text,
            style=style, vertex="1", parent=parent_id
        )
        self._create_mx_geometry(cell,
            x=str(x), y=str(y),
            width=str(width * self._axis_font_size * 0.6), height="20"
        )

    def _get_text_style(self) -> str:
        """
        Constructs a style string for text labels in draw.io format.

        Returns:
            str: A concatenated style string that defines appearance and behavior of text elements.
                Includes font settings, alignment, autosizing, and no stroke or fill colors.

                Example:
                "text;html=1;align=left;verticalAlign=middle;resizable=0;...;fontFamily=Arial;fontSize=12;"

        Behavior:
            - Enables HTML rendering for text.
            - Sets text alignment to left and vertically centered.
            - Disables resizing and connections.
            - Ensures clean appearance with no border or background fill.
            - Applies current font family and axis font size.

        Used in:
            - `_add_label()` to style axis or annotation text elements.
        """
        return "".join((
            "text;", "html=1;", "align=left;", "verticalAlign=middle;",
            "resizable=0;", "points=[];", "autosize=1;",
            "strokeColor=none;", "fillColor=none;",
            f"fontFamily={self._font_family};",
            f"fontColor=#000;", f"fontSize={self._axis_font_size};"
        ))
    
    def _get_numbering_style(self) -> str:
        """
        Generates a style string for numbering labels in draw.io format.

        Returns:
            str: A style string that defines the visual appearance of a numbering label.
                Includes background color, font size, and HTML rendering.

                Example:
                "rounded=0;whiteSpace=wrap;html=1;strokeColor=none;fillColor=black;fontSize=24;"

        Behavior:
            - Disables rounded corners and stroke outlines.
            - Enables HTML text rendering and word wrapping.
            - Applies background fill color using `_signature_color`.
            - Sets font size from `_signature_font_size`.

        Used in:
            - `_add_numbering()` to style index or label annotations on images.
        """
        return "".join((
            "rounded=0;", "whiteSpace=wrap;", "html=1;", "strokeColor=none;",
            f"fillColor={self._signature_color};",
            f"fontSize={self._signature_font_size};"
        ))

    def _get_numbering_text(self, label: str) -> str:
        """
        Generates an HTML-formatted string for a numbering label in draw.io.

        Args:
            label (str): The label text to be displayed (e.g., a number or character).

        Returns:
            str: An HTML string using a <font> tag with the configured font family and text color.
                Example: '<font face="Arial" style="color: white;">1</font>'

        Behavior:
            - Uses the current `_font_family` and `_signature_label_color` to format the label.
            - Intended for use with draw.io's HTML rendering in `mxCell.value`.

        Used in:
            - `_add_numbering()` when embedding label text into image annotations.
        """
        return f'<font face="{self._font_family}" style="color: {self._signature_label_color};">{label}</font>'

    def export_to_drawio(self, file: str | Path, **kwargs):
        """
        Exports the composed diagram structure to a .drawio-compatible XML file.

        Args:
            file (str | Path): The output file path where the XML content will be saved.
            **kwargs: Additional keyword arguments passed to `united_images()` 
                    (e.g., layout, spacing, width, height).

        Behavior:
            - Calls `united_images()` to arrange and prepare the diagram content.
            - Serializes the internal `_root` XML tree into indented draw.io format.
            - Writes the final XML string to the specified file with UTF-8 encoding.

        Notes:
            - The output file can be opened directly in draw.io or diagrams.net.
            - The layout and formatting of images are controlled via kwargs.

        Used in:
            - External scripts or UI to generate and save a final visual diagram.
        """
        self.united_images(**kwargs)

        tree = ET.ElementTree(self._root)
        ET.indent(tree, space="    ", level=0)
        tree.write(file, encoding="utf-8", xml_declaration=True)

    @staticmethod
    def _generate_id(prefix: str = "E__", 
                     suffix: str = "-1") -> str:
        """
        Generates a unique ID string for use in draw.io element attributes.

        Args:
            prefix (str, optional): Prefix to prepend to the ID. Defaults to "E__".
            suffix (str, optional): Suffix to append to the ID. Defaults to "-1".

        Returns:
            str: A unique string composed of the prefix, a base64-encoded UUID segment,
                and the suffix. Example: "E__abc123xyz-1"

        Behavior:
            - Uses the first 9 bytes of a UUID4 as the base for the ID.
            - Encodes it using URL-safe base64 and removes padding.

        Used in:
            - Element creation functions to assign distinct and consistent IDs to mxCells.
        """
        uid = uuid.uuid4().bytes[:9]
        base64_id = base64.urlsafe_b64encode(uid).decode("ascii").rstrip("=")
        return f"{prefix}{base64_id}{suffix}"

    @staticmethod
    def _image_to_base64(image: Image.Image) -> str:
        """
        Converts a PIL Image to a base64-encoded PNG string.

        Args:
            image (Image.Image): The PIL Image object to encode.

        Returns:
            str: A base64-encoded string representing the image in PNG format.
                Suitable for embedding directly in draw.io XML as a data URI.

        Behavior:
            - Saves the image to an in-memory bytes buffer in PNG format.
            - Encodes the buffer to base64 and decodes it to an ASCII string.

        Used in:
            - `preprocessing_image()` to embed images into the `mxCell` style attribute.
        """
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("ascii")
