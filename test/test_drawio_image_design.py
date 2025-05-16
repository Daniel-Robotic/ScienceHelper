import pytest
import xml.etree.ElementTree as ET
from PIL import Image
from image_processing.enumerates import SignaturePosition, LabelMode
from image_processing import DrawioImageDesign


class MockDrawioImageDesign(DrawioImageDesign):
    def __init__(self):
        self._images_path = ""
        self._images = [Image.new("RGB", (320, 270), "white")]

        self._font_family = "Arial"
        self._signature_label_color = "white"
        self._signature_color = "black"
        self._signature_font_size = 24
        self._signature_size = (40, 40)
        self._border_size = (10, 10, 10, 10)
        self._border_fill = "#000"
        self._signature = True
        self._signature_label = True
        self._signature_pos = SignaturePosition.TOP_RIGHT
        self._draw_axis = False

        self._axis_font_size = 12
        self._axis_length = 60
        self._axis_width = 1
        self._axis_offset = (30, 30)
        self._axis_labels = ("X", "Y")

        self._root = None
        self._xml_root = None
        self._create_drawio_structure()

    def _resize_proportional(self, image, width, height):
        if width is None or height is None:
            return image
        return image.resize((width, height))

    def _load_images(self, path):
        return self._images


@pytest.fixture
def design():
    d = MockDrawioImageDesign()
    d._signature_label = LabelMode.CYRILLIC_LOWER  # Исправление ошибки сигнатуры
    return d


def test_add_numbering_creates_cell(design):
    design._add_numbering(image_w=320, image_h=270, label="1", parent_id="testparent")
    cell = next((e for e in design._xml_root if e.attrib.get("parent") == "testparent" and e.attrib.get("id", "").endswith("-numbering")), None)

    assert cell is not None
    assert cell.attrib.get("vertex") == "1"
    assert "html=1" in cell.attrib.get("style", "")
    assert '<font' in cell.attrib.get("value", "")
    assert cell.find("mxGeometry") is not None


def test_preprocessing_image_adds_cells(design):
    design.preprocessing_image(index=0, width=320, height=270, position_x=10, position_y=20)

    image_cells = [e for e in design._xml_root if "shape=image;" in e.attrib.get("style", "")]
    assert len(image_cells) == 1

    img_cell = image_cells[0]
    geom = img_cell.find("mxGeometry")
    assert geom.attrib["x"] == "10"
    assert geom.attrib["y"] == "20"

    numbering_cell = next((e for e in design._xml_root if e.attrib.get("parent") == img_cell.attrib["id"] and e.attrib.get("id", "").endswith("-numbering")), None)
    assert numbering_cell is not None


def test_generate_id_format():
    id_ = DrawioImageDesign._generate_id()
    assert id_.startswith("E__")
    assert id_.endswith("-1")


def test_add_axes_adds_group_and_elements(design):
    design._draw_axis = True
    design._axis_labels = ("Xlabel", "Ylabel")
    design._add_axes(image_w=320, image_h=270, label_x="Xlabel", label_y="Ylabel", parent_id="1")

    group_cell = next((e for e in design._xml_root if e.attrib.get("style") == "group" and e.attrib.get("parent") == "1"), None)
    assert group_cell is not None

    labels = [e for e in design._xml_root if e.attrib.get("parent") == group_cell.attrib["id"] and "text;" in e.attrib.get("style", "")]
    assert len(labels) == 2

    arrows = [e for e in design._xml_root if e.attrib.get("parent") == group_cell.attrib["id"] and e.attrib.get("edge") == "1"]
    assert len(arrows) == 2


def test_layout_images_row_mode(design):
    design._layout_images(layout="row", spacing=5)
    group = next((e for e in design._xml_root if e.attrib.get("style") == "group"), None)
    assert group is not None
    assert group.find("mxGeometry") is not None


def test_layout_images_column_mode(design):
    design._layout_images(layout="column", spacing=10)
    group = next((e for e in design._xml_root if e.attrib.get("style") == "group"), None)
    assert group is not None
    assert group.find("mxGeometry") is not None


def test_united_images_combines_images(design):
    design.united_images(layout="row", spacing=0, width=100, height=100)
    group_cell = next((e for e in design._xml_root if e.attrib.get("style") == "group" and e.attrib.get("parent") == "1"), None)
    assert group_cell is not None


def test_create_mx_cell_and_geometry(design):
    cell = design._create_mx_cell(id="test", value="testval", style="teststyle", vertex="1", parent="1")
    geom = design._create_mx_geometry(cell, x="10", y="20", width="30", height="40")
    assert cell.tag == "mxCell"
    assert geom.tag == "mxGeometry"


def test_add_label_creates_text_cell(design):
    design._add_label("label1", "Text", x=100, y=200, width=10, parent_id="1", style="text;html=1;")
    label = next((e for e in design._xml_root if e.attrib.get("id") == "label1"), None)
    assert label is not None
    assert "html=1" in label.attrib.get("style", "")
