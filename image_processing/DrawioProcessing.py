import io 
import math
import uuid
import base64
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Union

from PIL import Image
from image_processing.enumerates import *
from image_processing.ImageProcessing import ImageProcessing, get_label


class DrawioImageDesign(ImageProcessing):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._images = self._load_images(self._images_path)

        self._images = self._load_images(self._images_path)

        self._root = None 
        self._xml_root = None
        self._create_drawio_structure()

    # Методы родительского класса
    def _draw_border(self):
        return f"imageBorder={self._border_fill};strokeWidth={max(self._border_size)};"

    def _add_numbering(self): pass

    def _add_axes(self): pass
        
    def _layout_images(self): pass

    def preprocessing_image(self,
                            index: int,
                            width: int = None,
                            height: int = None,
                            position_x: int = 0,
                            position_y: int = 0):
        
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

        mxCell = ET.SubElement(self._xml_root, "mxCell",
                               id=cell_id, value="",
                               style="".join(style),
                               vertex="1", parent="1"
                              )
        mxGeometry = ET.SubElement(mxCell, "mxGeometry",
                                    x=str(position_x), 
                                    y=str(position_y),
                                    width=str(image_w), 
                                    height=str(image_h))
        mxGeometry.set("as", "geometry")
    
    def united_images(self): pass

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

    @staticmethod
    def _generate_id(prefix: str = "E__", 
                     suffix: str = "-1") -> str:
        uid = uuid.uuid4().bytes[:9]
        base64_id = base64.urlsafe_b64encode(uid).decode("ascii").rsplit("=")
        return f"{prefix}{base64_id[0]}{suffix}"

    @staticmethod
    def _image_to_base64(image: Image.Image) -> str:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("ascii")


    # def export_to_drawio(self, file: str | Path, **kwargs):
    #     ET.indent(tree, space="  ", level=0) 
    #     Path(file).write_text(self.united_images(**kwargs), encoding="utf-8")
