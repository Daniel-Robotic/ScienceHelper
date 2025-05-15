import io, math, uuid, base64, xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Union

from PIL import Image
from image_processing.enumerates import *
from image_processing.ImageProcessing import ImageProcessing, get_label


class DrawioImageDesign(ImageProcessing):
    # ───────────────────────────────────────────────────────── #
    #  INIT
    # ───────────────────────────────────────────────────────── #
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._images = self._load_images(self.images_path)

    # ───────────────────────────────────────────────────────── #
    #  HELPERS
    # ───────────────────────────────────────────────────────── #
    @staticmethod
    def _pil_to_b64(img: Image.Image) -> str:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("ascii")

    @staticmethod
    def _add_geom(cell: ET.Element, **coords):
        g = ET.SubElement(cell, "mxGeometry", **{k: str(v) for k, v in coords.items()})
        g.set("as", "geometry")
        return g

    # толщина + цвет рамки
    def _border_params(self) -> tuple[int, str]:
        if isinstance(self.border_size, int):
            bw = self.border_size
        else:                                          # (l,t,r,b) → max
            bw = max(self.border_size)
        color = (('#%02x%02x%02x' % self.border_fill)      # RGB → #rrggbb
                 if isinstance(self.border_fill, tuple)
                 else self.border_fill)
        return bw, color

    # ───────────────────────────────────────────────────────── #
    #  PRE-PROCESS (без прорисовки рамки!)
    # ───────────────────────────────────────────────────────── #
    def _draw_border(self, img: Image.Image) -> Image.Image:
        return img                                      # рамку добавит draw.io

    def preprocessing_image(self, idx: int,
                            width: int | None = None,
                            height: int | None = None) -> Image.Image:
        img = self._images[idx]
        return self._resize_proportional(img, width, height)

    # ───────────────────────────────────────────────────────── #
    #  LAYOUT
    # ───────────────────────────────────────────────────────── #
    def _layout_images(self, layout: Union[str, LayoutMode],
                       spacing: int,
                       cols: Optional[int],
                       rows: Optional[int]) -> list[tuple[int, int]]:
        layout = layout.value if isinstance(layout, LayoutMode) else layout
        pos: list[tuple[int, int]] = []

        if layout == "row":
            x = y = 0
            for im in self._images:
                pos.append((x, y))
                x += im.width + spacing

        elif layout == "column":
            x = y = 0
            for im in self._images:
                pos.append((x, y))
                y += im.height + spacing

        elif layout == "grid":
            cols = cols or math.ceil(math.sqrt(len(self._images)))
            img_w = self._images[0].width + spacing
            img_h = self._images[0].height + spacing
            for i, _ in enumerate(self._images):
                pos.append(((i % cols) * img_w,
                            (i // cols) * img_h))
        else:
            raise ValueError(f"Unknown layout: {layout}")

        return pos

    # ───────────────────────────────────────────────────────── #
    #  LABEL  &  AXES   (внутри группы)
    # ───────────────────────────────────────────────────────── #
    def _add_numbering(self, xml_root: ET.Element, parent_id: str,
                       text: str, dx: float, dy: float):
        lbl = ET.SubElement(xml_root, "mxCell",
                            id=str(uuid.uuid4()), value=text,
                            style=f"shape=label;align=left;verticalAlign=top;"
                                  f"fontSize={self.signature_font_size};"
                                  f"fontColor={self.signature_label_color};"
                                  f"fillColor=none;strokeColor=none;",
                            vertex="1", parent=parent_id)
        self._add_geom(lbl, x=dx, y=dy,
                       width=self.signature_size[0],
                       height=self.signature_size[1])

    def _add_axes(self, xml_root: ET.Element, parent_id: str,
                  w: int, h: int,
                  label_x: str, label_y: str):
        off_x, off_y = (self.axis_offset if isinstance(self.axis_offset, tuple)
                        else (self.axis_offset, self.axis_offset))

        # линии-стрелки
        for _ in range(2):
            line = ET.SubElement(xml_root, "mxCell",
                                 id=str(uuid.uuid4()),
                                 style=f"endArrow=block;strokeWidth={self.axis_width};",
                                 edge="1", parent=parent_id)
            self._add_geom(line, relative="1")

        # подписи
        self._add_numbering(xml_root, parent_id,
                            label_x, off_x + self.axis_length, h - self.axis_font_size - 4)
        self._add_numbering(xml_root, parent_id,
                            label_y, 4, off_y)

    # ───────────────────────────────────────────────────────── #
    #  BUILD XML
    # ───────────────────────────────────────────────────────── #
    def united_images(self,
                      layout: Union[str, LayoutMode] = "row",
                      spacing: int = 10,
                      grid_cols: Optional[int] = None,
                      grid_rows: Optional[int] = None,
                      width: int | None = None,
                      height: int | None = None) -> str:

        root = ET.Element("mxfile", host="app.diagrams.net")
        diagram = ET.SubElement(root, "diagram", name="Page-1", id=str(uuid.uuid4()))
        model = ET.SubElement(diagram, "mxGraphModel")
        xml_root = ET.SubElement(model, "root")
        ET.SubElement(xml_root, "mxCell", id="0")
        ET.SubElement(xml_root, "mxCell", id="1", parent="0")

        bw, bc = self._border_params()                # толщина и цвет рамки
        positions = self._layout_images(layout, spacing, grid_cols, grid_rows)

        for idx, (px, py) in enumerate(positions):
            img = self.preprocessing_image(idx, width, height)

            # Группа
            g_id = str(uuid.uuid4())
            group = ET.SubElement(xml_root, "mxCell",
                                  id=g_id, value="", vertex="1", parent="1")
            self._add_geom(group,
                           x=px, y=py,
                           width=img.width + bw * 2,
                           height=img.height + bw * 2)

            # Изображение
            style = (f"shape=image;strokeWidth={bw};strokeColor={bc};"
                     "aspect=fixed;imageAspect=0;"
                     f"image=data:image/png,{self._pil_to_b64(img)}")
            img_cell = ET.SubElement(xml_root, "mxCell",
                                     id=str(uuid.uuid4()), value="",
                                     style=style, vertex="1", parent=g_id)
            self._add_geom(img_cell, x=bw, y=bw,
                           width=img.width, height=img.height)

            # Подпись
            if self.signature:
                self._add_numbering(xml_root, g_id,
                                    get_label(idx, self.signature_label),
                                    dx=4, dy=4)

            # Оси
            if self.draw_axis:
                lx = (self.axis_labels[0] if isinstance(self.axis_labels[0], str)
                      else self.axis_labels[0][idx])
                ly = (self.axis_labels[1] if isinstance(self.axis_labels[1], str)
                      else self.axis_labels[1][idx])
                self._add_axes(xml_root, g_id, img.width, img.height, lx, ly)

        return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")

    # ───────────────────────────────────────────────────────── #
    #  EXPORT
    # ───────────────────────────────────────────────────────── #
    def export_to_drawio(self, file: str | Path, **kwargs):
        Path(file).write_text(self.united_images(**kwargs), encoding="utf-8")
