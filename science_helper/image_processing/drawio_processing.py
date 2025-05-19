import base64
import io
from pathlib import Path
import uuid
import xml.etree.ElementTree as ET

from PIL import Image

from science_helper.image_processing.enumerates import LayoutMode, SignaturePosition
from science_helper.image_processing.processing import ImageProcessing


class DrawioImageDesign(ImageProcessing):
    """A class for generating image-based diagrams in draw.io (mxGraph XML) format.

    This class extends `ImageProcessing` and transforms a list of images into a structured
    `.drawio` XML diagram with features such as borders, numbering (labels), and coordinate axes.
    Each image is embedded as a base64-encoded PNG and arranged in a specified layout.

    Key Features:
        - Embeds images in draw.io format with layout control (row, column, grid).
        - Adds numbered labels with configurable position, font, and color.
        - Optionally includes X and Y axes with labels and arrowheads.
        - Exports the result as a `.drawio`-compatible XML file.

    Usage:
        >>> designer = DrawioImageDesign(images_path="images/")
        >>> designer.export_to_drawio("result.drawio", layout="grid", spacing=20)

    Raises:
        IndexError: If image indices exceed available range.
        ValueError: If an unsupported layout mode is used.
        OSError: If font files cannot be loaded.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the DrawioImageDesign class with inherited image processing settings.

        This constructor extends the base class `ImageProcessing` and prepares additional internal
        structures required for generating a `.drawio` diagram.

        Behavior:
            - Loads images from the given path using `_load_images`.
            - Initializes XML elements `_root` and `_xml_root` for the draw.io diagram.
            - Calls `_create_drawio_structure()` to prepare the base diagram layout.

        Args:
            *args: Positional arguments passed to the `ImageProcessing` superclass.
            **kwargs: Keyword arguments passed to the `ImageProcessing` superclass.

        Raises:
            FileNotFoundError: If the specified image directory does not exist.
            PIL.UnidentifiedImageError: If any image file is unreadable.
        """
        super().__init__(*args, **kwargs)
        self._images = self._load_images(self._images_path)

        self._root = None
        self._xml_root = None
        self._create_drawio_structure()

    # Методы родительского класса
    def _draw_border(self):
        """Generate the draw.io style string for image borders.

        This method creates a style string used in the `mxCell` element of draw.io to define
        the appearance of image borders, including color and stroke width.

        Returns:
            str: A style string with `imageBorder` color and `strokeWidth` values based on
                the instance's `_border_fill` and `_border_size`.

        Example:
            "imageBorder=black;strokeWidth=10;"
        """
        return f"imageBorder={self._border_fill};strokeWidth={max(self._border_size)};"

    def _add_numbering(self, image_w: int, image_h: int, label: str = "", parent_id: str = "1"):
        """Add a label (numbering) to the image in the draw.io structure.

        This method adds a label as an `mxCell` element positioned relative to the image,
        based on the configured signature position and offset. It is commonly used to
        annotate images with index numbers or custom labels.

        Args:
            image_w (int): Width of the image in pixels.
            image_h (int): Height of the image in pixels.
            label (str, optional): The text label to be displayed. Defaults to "".
            parent_id (str, optional): ID of the parent `mxCell` element. Defaults to "1".

        Behavior:
            - Computes the label position based on `_signature_pos` and `_border_size`.
            - Uses `_get_numbering_text()` to format the label text as HTML.
            - Uses `_get_numbering_style()` to apply styling to the label.
            - Adds the label to the internal draw.io XML under the given parent.

        Raises:
            KeyError: If `_signature_pos` is not a recognized key in `pos_map`.

        Used in:
            - `preprocessing_image()` to place automatic or custom labels on each image.
        """
        x0, y0, _, _ = self._get_positions(image_w, image_h)
        offset = max(self._border_size)
        key = (
            self._signature_pos.value
            if isinstance(self._signature_pos, SignaturePosition)
            else self._signature_pos
        )

        pos_map = {
            SignaturePosition.TOP_LEFT.value: (-offset, -offset),
            SignaturePosition.TOP_RIGHT.value: (offset, -offset),
            SignaturePosition.BOTTOM_LEFT.value: (-offset, offset),
            SignaturePosition.BOTTOM_RIGHT.value: (offset, offset),
        }

        dx, dy = pos_map.get(key, (0, 0))
        x0 += dx
        y0 += dy

        cell = self._create_mx_cell(
            id=self._generate_id(suffix="-numbering"),
            value=self._get_numbering_text(label),
            style=self._get_numbering_style(),
            vertex="1",
            parent=parent_id,
        )

        self._create_mx_geometry(
            cell,
            x=str(x0),
            y=str(y0),
            width=str(self._signature_size[0]),
            height=str(self._signature_size[1]),
        )

    def _add_axes(
        self, image_w: int, image_h: int, label_x: str, label_y: str, parent_id: str = "1"
    ):
        """Add coordinate axes with labels to an image block in the draw.io structure.

        This method draws X and Y axes as lines with arrowheads and places corresponding
        text labels using `mxCell` elements. All components are grouped under a parent
        cell to maintain logical structure.

        Args:
            image_w (int): Width of the image in pixels.
            image_h (int): Height of the image in pixels.
            label_x (str): Label text for the X-axis.
            label_y (str): Label text for the Y-axis.
            parent_id (str, optional): ID of the parent `mxCell` group. Defaults to "1".

        Behavior:
            - Computes the position for axis origin based on `self._axis_offset`.
            - Calculates required dimensions to fit arrows and labels.
            - Creates a group `mxCell` container to hold both axes and their labels.
            - Uses `_create_axis` for each axis line with arrowheads.
            - Uses `_add_label` to place labels near the arrow tips.

        Notes:
            - The entire axis group is positioned relative to the bottom-left corner of the image.
            - The label sizes are computed based on their length and font size.
            - Useful for indicating orientation or scale in diagrams.

        Used in:
            - `preprocessing_image()` if `self._draw_axis` is enabled.
        """
        offset_x, offset_y = (
            (self._axis_offset, self._axis_offset)
            if isinstance(self._axis_offset, int)
            else self._axis_offset
        )

        label_x_width = len(label_x) * self._axis_font_size * 0.6
        label_y_height = len(label_y) * self._axis_font_size * 0.6

        width = self._axis_length + 5 + label_x_width
        height = self._axis_length + 5 + label_y_height

        group_id = self._generate_id(suffix="-axisgroup")
        style = self._get_text_style()

        group_cell = self._create_mx_cell(
            id=group_id, value="", style="group", vertex="1", connectable="0", parent=parent_id
        )
        self._create_mx_geometry(
            group_cell,
            x=str(offset_x),
            y=str(image_h - offset_y - height),
            width=str(width),
            height=str(height),
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
        self._add_label(
            ylabel_id, label_y, x0 + 5, y_end - self._axis_font_size, len(label_y), group_id, style
        )

    def _layout_images(
        self,
        layout: str = "row",
        spacing: int = 10,
        grid_cols: int | None = None,
        grid_rows: int | None = None,
    ):
        """Arrange images in a specified layout and embed them into the draw.io structure.

        This method computes the position for each image based on the chosen layout
        ("row", "column", or "grid") and embeds them into the internal draw.io XML structure.
        It also creates a group `mxCell` that contains all image elements.

        Args:
            layout (str, optional): Layout mode. Must be one of:
                - "row": images in a single horizontal line.
                - "column": images in a vertical column.
                - "grid": images arranged in a rectangular grid.
                Defaults to "row".
            spacing (int, optional): Space in pixels between images. Defaults to 10.
            grid_cols (Optional[int], optional): Number of columns for grid layout.
                Required if `layout == "grid"` and `grid_rows` is not specified.
            grid_rows (Optional[int], optional): Number of rows for grid layout.
                Required if `layout == "grid"` and `grid_cols` is not specified.

        Behavior:
            - Computes (x, y) positions for each image depending on layout type.
            - Calls `preprocessing_image()` for each image with computed coordinates.
            - Wraps all images into a single group cell (`mxCell`) in the diagram.
            - Calculates the group's total width and height to contain all images.

        Raises:
            ValueError: If `layout` is not one of the supported types.

        Used in:
            - `united_images()` to organize all images into a coherent visual structure.
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
            cols = grid_cols or int(n**0.5)
            grid_rows or ((n + cols - 1) // cols)
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
            id=group_id, value="", style="group", vertex="1", connectable="0", parent="1"
        )

        all_right = []
        all_bottom = []
        for i, (x, y) in enumerate(positions):
            self.preprocessing_image(index=i, position_x=x, position_y=y, parent_id=group_id)
            all_right.append(x + image_w)
            all_bottom.append(y + image_h)

        self._create_mx_geometry(
            group_cell, x="30", y="30", width=str(max(all_right)), height=str(max(all_bottom))
        )

    def preprocessing_image(  # noqa: PLR0913
        self,
        index: int,
        width: int | None = None,
        height: int | None = None,
        position_x: int = 0,
        position_y: int = 0,
        parent_id: str = "1",
    ):
        """Process and embed a single image into the draw.io XML structure.

        This method performs image resizing, base64 encoding, and creates an <mxCell> element
        that represents the image in the draw.io diagram. Optional features such as labeling and
        axes are also added if configured.

        Args:
            index (int): Index of the image in the internal list to process.
            width (Optional[int]): Desired width of the image. If set, used for proportional resizing.
            height (Optional[int]): Desired height of the image. If set, used for proportional resizing.
            position_x (int, optional): X-coordinate for placing the image. Defaults to 0.
            position_y (int, optional): Y-coordinate for placing the image. Defaults to 0.
            parent_id (str, optional): ID of the parent mxCell in the draw.io structure. Defaults to "1".

        Behavior:
            - Resizes the image proportionally if `width` or `height` is provided.
            - Encodes the image in base64 PNG format for draw.io embedding.
            - Creates an <mxCell> with style for image appearance and positioning.
            - Optionally adds:
                - a numbering label using `_add_numbering()`,
                - X and Y axes using `_add_axes()`.

        Raises:
            IndexError: If the specified index is out of bounds of the internal image list.

        Used in:
            - `_layout_images()` for arranging multiple images.
            - `united_images()` for full diagram generation.
        """  # noqa: E501
        if index >= len(self._images):
            raise IndexError(f"Index {index} outside the range of the image list")

        image = self._resize_proportional(self._images[index], width, height)
        image_w, image_h = image.size

        image_base64 = self._image_to_base64(image)
        cell_id = self._generate_id(suffix=f"-{index + 1}")

        style = (
            "shape=image;",
            "verticalLabelPosition=bottom;",
            "labelBackgroundColor=default;",
            "verticalAlign=top;",
            "aspect=fixed;",
            "imageAspect=0;",
            f"image=data:image/png,{image_base64};",
            self._draw_border(),
        )

        cell = self._create_mx_cell(
            id=cell_id, value="", style="".join(style), vertex="1", parent=parent_id
        )

        self._create_mx_geometry(
            cell, x=str(position_x), y=str(position_y), width=str(image_w), height=str(image_h)
        )

        if self._signature and self._signature_label:
            self._add_numbering(
                image_w=image_w,
                image_h=image_h,
                label=self._get_label(index=index),
                parent_id=cell_id,
            )

        if self._draw_axis:
            lx, ly = self._axis_labels
            lx, ly = (lx[index], ly[index]) if isinstance(lx, tuple) else (lx, ly)
            self._add_axes(image_w, image_h, label_x=lx, label_y=ly, parent_id=cell_id)

    def united_images(  # noqa: PLR0913
        self,
        layout: str | LayoutMode = "row",
        spacing: int = 10,
        grid_cols: int | None = None,
        grid_rows: int | None = None,
        width: int | None = None,
        height: int | None = None,
    ):
        """Compose and layout all images into a draw.io diagram structure.

        This method prepares the diagram by optionally resizing all images, arranging them
        according to the specified layout (row, column, or grid), and embedding them as mxCell
        elements into the XML structure used by draw.io.

        Args:
            layout (Union[str, LayoutMode], optional): Layout strategy for arranging images.
                Can be "row", "column", or "grid". Defaults to "row".
            spacing (int, optional): Space in pixels between images. Defaults to 10.
            grid_cols (Optional[int], optional): Number of columns in the grid layout.
                Only used if layout is "grid".
            grid_rows (Optional[int], optional): Number of rows in the grid layout.
                Only used if layout is "grid".
            width (Optional[int], optional): Target width for resizing all images.
            height (Optional[int], optional): Target height for resizing all images.

        Behavior:
            - Resizes all images if `width` or `height` is provided.
            - Computes layout positions for each image.
            - Calls `preprocessing_image()` for each image to embed it into the diagram.
            - All images are grouped under a parent mxCell in the XML structure.

        Used in:
            - `export_to_drawio()` to generate the final .drawio file.
        """
        layout = layout.value if isinstance(layout, LayoutMode) else layout

        if width or height:
            self._images = [
                self._resize_proportional(img, width=width, height=height) for img in self._images
            ]

        self._layout_images(
            layout=layout, spacing=spacing, grid_cols=grid_cols, grid_rows=grid_rows
        )

    # методы этого класса
    def _create_drawio_structure(self):
        """Initialize the root XML structure for the draw.io diagram.

        This method sets up the required elements for a valid draw.io file:
        - Creates the `<mxfile>` root element with the host attribute.
        - Adds a `<diagram>` element with a unique ID and a default name ("Обработчик изображений").
        - Constructs the `<mxGraphModel>` and its nested `<root>` element.
        - Inserts two base `<mxCell>` elements:
            - ID "0": the invisible root container.
            - ID "1": the main layer where all diagram elements will be attached.

        This function must be called before adding any visual elements (e.g., images, labels, arrows).
        """  # noqa: E501
        self._root = ET.Element("mxfile", host="ScienceHelper")

        diagram_id = self._generate_id(prefix="", suffix="")
        diagram = ET.SubElement(self._root, "diagram", name="Обработчик изображений", id=diagram_id)

        model = ET.SubElement(diagram, "mxGraphModel")
        self._xml_root = ET.SubElement(model, "root")

        ET.SubElement(self._xml_root, "mxCell", id="0")
        ET.SubElement(self._xml_root, "mxCell", id="1", parent="0")

    def _create_mx_cell(self, **attrs) -> ET.Element:
        """Create and append an <mxCell> element to the draw.io XML structure.

        Args:
            **attrs: Arbitrary keyword arguments representing attributes for the <mxCell> element,
                    such as id, value, style, parent, vertex, edge, etc.

        Returns:
            ET.Element: The newly created <mxCell> element, attached to the internal XML root.

        Notes:
            - This method is used to define visual elements like images, groups, arrows, or text boxes.
            - The element is added directly to `self._xml_root`.
        """  # noqa: E501
        return ET.SubElement(self._xml_root, "mxCell", **attrs)

    def _create_mx_geometry(self, parent: ET.Element, **attrs) -> ET.Element:
        """Create and attach an <mxGeometry> element to the given <mxCell> element.

        Args:
            parent (ET.Element): The parent <mxCell> element to which geometry should be added.
            **attrs: Arbitrary keyword arguments representing geometry attributes like x, y, width, height, etc.

        Returns:
            ET.Element: The created <mxGeometry> element with the attribute `as="geometry"`.

        Notes:
            - This method is used to define size and position for visual elements in draw.io.
            - The geometry is added as a child of the given parent <mxCell>.
        """  # noqa: E501
        geom = ET.SubElement(parent, "mxGeometry", **attrs)
        geom.set("as", "geometry")
        return geom

    def _create_axis(self,  # noqa: PLR0913
                     id: str, 
                     x0: float, y0: float, 
                     x1: float, y1: float, 
                     parent_id: str):
        """Create a directional axis line in the draw.io XML structure.

        This method creates an `mxCell` representing an axis (X or Y) with an arrowhead,
        then adds source and target points to define the line geometry.

        Args:
            id (str): Unique identifier for the created axis element.
            x0 (float): X-coordinate of the starting point.
            y0 (float): Y-coordinate of the starting point.
            x1 (float): X-coordinate of the ending point.
            y1 (float): Y-coordinate of the ending point.
            parent_id (str): ID of the parent group or cell to attach this axis to.

        Notes:
            - The axis is styled with a thin block arrow and fixed stroke width.
            - Coordinates are embedded as `mxPoint` elements inside `mxGeometry`.
            - The geometry is marked with `relative="1"` to support group-based positioning.
        """
        cell = self._create_mx_cell(
            id=id,
            value="",
            style=f"endArrow=blockThin;html=1;rounded=0;strokeWidth={self._axis_width}",
            edge="1",
            parent=parent_id,
        )

        geom = self._create_mx_geometry(cell, width="50", height="50", relative="1")

        source = ET.SubElement(geom, "mxPoint", x=str(x0), y=str(y0))
        target = ET.SubElement(geom, "mxPoint", x=str(x1), y=str(y1))

        source.set("as", "sourcePoint")
        target.set("as", "targetPoint")

    def _add_label(self,  # noqa: PLR0913
                   cell_id: str, text: str, 
                   x: float, y: float, 
                   width: int, parent_id: str, 
                   style: str
    ):
        """Add a text label to the draw.io XML structure at a specific position.

        This method creates a vertex `mxCell` element that displays the provided text
        with the given styling and places it at the specified (x, y) coordinates.

        Args:
            cell_id (str): Unique identifier for the created label cell.
            text (str): Text content to display.
            x (float): X-coordinate of the label’s top-left corner.
            y (float): Y-coordinate of the label’s top-left corner.
            width (int): Logical width of the text (multiplied by font size to calculate actual width).
            parent_id (str): ID of the parent `mxCell` to which the label belongs.
            style (str): Styling string defining appearance (font, alignment, color, etc.).

        Notes:
            - Label size is computed using `width * font_size * 0.6` as an estimate.
            - The label is placed using `mxGeometry` and added as a child of the specified parent.
            - Suitable for labeling axes or other elements in the diagram.
        """  # noqa: E501
        cell = self._create_mx_cell(
            id=cell_id, value=text, style=style, vertex="1", parent=parent_id
        )
        self._create_mx_geometry(
            cell, x=str(x), y=str(y), width=str(width * self._axis_font_size * 0.6), height="20"
        )

    def _get_text_style(self) -> str:
        """Generate a draw.io-compatible style string for text labels.

        Constructs a style definition string used for labeling axes and other elements
        in the diagram. This string includes alignment, font settings, and visual options.

        Returns:
            str: A concatenated style string, e.g., suitable for use in an `mxCell`
            with text content. It includes parameters like `fontFamily`, `fontSize`,
            `html`, `align`, `strokeColor`, etc.

        Notes:
            - The font family is set using `self._font_family`.
            - The font size is defined by `self._axis_font_size`.
            - Text is styled to be HTML-rendered, unresizable, and with no background or stroke.
            - Used in `_add_label()` to consistently format axis and annotation labels.
        """
        return "".join(
            (
                "text;",
                "html=1;",
                "align=left;",
                "verticalAlign=middle;",
                "resizable=0;",
                "points=[];",
                "autosize=1;",
                "strokeColor=none;",
                "fillColor=none;",
                f"fontFamily={self._font_family};",
                "fontColor=#000;",
                f"fontSize={self._axis_font_size};",
            )
        )

    def _get_numbering_style(self) -> str:
        """Generate a style string for draw.io numbering labels.

        Constructs a draw.io-compatible style string that defines the appearance
        of a label used for numbering or annotating images (e.g., image index or name).

        Returns:
            str: A style string that includes options for rounded corners,
            text wrapping, HTML rendering, and font settings such as background
            fill color and font size.

        Notes:
            - The fill color is defined by `self._signature_color`.
            - The font size is defined by `self._signature_font_size`.
            - Used in `_add_numbering()` to style the label block.
        """
        return "".join(
            (
                "rounded=0;",
                "whiteSpace=wrap;",
                "html=1;",
                "strokeColor=none;",
                f"fillColor={self._signature_color};",
                f"fontSize={self._signature_font_size};",
            )
        )

    def _get_numbering_text(self, label: str) -> str:
        """Generate an HTML-formatted text string for a numbering label in draw.io.

        Args:
            label (str): The label content to display (e.g., a letter or number).

        Returns:
            str: An HTML string that wraps the label in a <font> tag with the configured
            font family and text color. This string is suitable for inclusion in the
            `value` attribute of a draw.io `mxCell`.

        Notes:
            - The font face is taken from `self._font_family`.
            - The text color is taken from `self._signature_label_color`.
            - Used in `_add_numbering()` to render the label inside the image block.
        """
        return f'<font face="{self._font_family}" style="color: {self._signature_label_color};">{label}</font>'  # noqa: E501

    def export_to_drawio(self, file: str | Path, **kwargs):
        """Export the current image layout to a .drawio-compatible XML file.

        Args:
            file (str | Path): Path to the output .drawio file.
            **kwargs: Additional keyword arguments passed to `united_images()` 
                (e.g., layout, spacing, grid_cols, grid_rows, width, height).

        Behavior:
            - Calls `united_images()` to build the diagram structure.
            - Serializes the internal XML structure into draw.io-compatible format.
            - Writes the result to the specified file in UTF-8 encoding.

        Raises:
            ValueError: If layout or content is invalid during composition.
        
        Notes:
            - The output file can be opened directly in draw.io or diagrams.net.
            - This method must be called after images are loaded and parameters configured.
        """
        self.united_images(**kwargs)

        tree = ET.ElementTree(self._root)
        ET.indent(tree, space="    ", level=0)
        tree.write(file, encoding="utf-8", xml_declaration=True)

    @staticmethod
    def _generate_id(prefix: str = "E__", suffix: str = "-1") -> str:
        """Generate a unique ID for draw.io XML elements.

        Args:
            prefix (str, optional): Prefix for the ID. Defaults to "E__".
            suffix (str, optional): Suffix for the ID. Defaults to "-1".

        Returns:
            str: A unique, base64-encoded identifier string.

        Notes:
            - Uses the first 9 bytes of a UUID4, encoded in URL-safe base64 format.
            - Padding is stripped from the encoded string.
            - Useful for generating unique IDs for mxCell elements in draw.io.
        """
        uid = uuid.uuid4().bytes[:9]
        base64_id = base64.urlsafe_b64encode(uid).decode("ascii").rstrip("=")
        return f"{prefix}{base64_id}{suffix}"

    @staticmethod
    def _image_to_base64(image: Image.Image) -> str:
        """Convert a PIL Image to a base64-encoded PNG string.

        Args:
            image (Image.Image): The image to convert.

        Returns:
            str: A base64-encoded string representing the PNG image.

        Notes:
            - The resulting string can be embedded in XML or HTML as a data URI.
            - Image is saved to an in-memory buffer before encoding.
        """
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("ascii")
