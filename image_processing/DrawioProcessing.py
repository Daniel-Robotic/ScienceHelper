import io 
import uuid
import base64
import xml.etree.ElementTree as ET
from typing import Optional, Union

from PIL import Image
from pathlib import Path
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
        return f"imageBorder={self._border_fill};strokeWidth={max(self._border_size)};"

    def _add_numbering(self,
                       image_w: int,
                       image_h: int,
                       label: str = "",
                       parent_id: str = "1"):
        
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
        
        layout = layout.value if isinstance(layout, LayoutMode) else layout
        
        if width or height:
            self._images = [self._resize_proportional(img, width=width, height=height) for img in self._images]
         
        self._layout_images(layout=layout,
                            spacing=spacing,
                            grid_cols=grid_cols,
                            grid_rows=grid_rows)

    # методы этого класса
    def _create_drawio_structure(self):
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
        return ET.SubElement(self._xml_root, "mxCell", **attrs)
    
    def _create_mx_geometry(self, parent: ET.Element, **attrs) -> ET.Element:
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
        
        cell = self._create_mx_cell(
            id=cell_id, value=text,
            style=style, vertex="1", parent=parent_id
        )
        self._create_mx_geometry(cell,
            x=str(x), y=str(y),
            width=str(width * self._axis_font_size * 0.6), height="20"
        )

    def _get_text_style(self) -> str:
        return "".join((
            "text;", "html=1;", "align=left;", "verticalAlign=middle;",
            "resizable=0;", "points=[];", "autosize=1;",
            "strokeColor=none;", "fillColor=none;",
            f"fontFamily={self._font_family};",
            f"fontColor=#000;", f"fontSize={self._axis_font_size};"
        ))
    
    def _get_numbering_style(self) -> str:
        return "".join((
            "rounded=0;", "whiteSpace=wrap;", "html=1;", "strokeColor=none;",
            f"fillColor={self._signature_color};",
            f"fontSize={self._signature_font_size};"
        ))

    def _get_numbering_text(self, label: str) -> str:
        return f'<font face="{self._font_family}" style="color: {self._signature_label_color};">{label}</font>'

    def export_to_drawio(self, file: str | Path, **kwargs):
        tree = ET.ElementTree(self._root)
        ET.indent(tree, space="    ", level=0)
        Path(file).write_text(self.united_images(**kwargs), encoding="utf-8")

    @staticmethod
    def _generate_id(prefix: str = "E__", 
                     suffix: str = "-1") -> str:
        uid = uuid.uuid4().bytes[:9]
        base64_id = base64.urlsafe_b64encode(uid).decode("ascii").rstrip("=")
        return f"{prefix}{base64_id}{suffix}"

    @staticmethod
    def _image_to_base64(image: Image.Image) -> str:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("ascii")
