import pytest
import xml.etree.ElementTree as ET
from PIL import Image
from image_processing.enumerates import SignaturePosition
from image_processing import DrawioImageDesign


class MockDrawioImageDesign(DrawioImageDesign):
    def __init__(self):
        # Эмуляция родительского состояния без вызова super().__init__()
        self._images_path = ""
        self._images = [Image.new("RGB", (320, 270), "white")]

        # Настройки подписи и рамки
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

        # XML-структура
        self._root = None
        self._xml_root = None
        self._create_drawio_structure()

    def _resize_proportional(self, image, width, height):
        return image.resize((width, height))

    def _load_images(self, path):
        return self._images



@pytest.fixture
def design():
    return MockDrawioImageDesign()


def test_add_numbering_creates_cell(design):
    design._add_numbering(image_w=320, image_h=270, label="1", parent_id="testparent")

    cell = next((e for e in design._xml_root if e.attrib.get("id") == "testparentnumbering"), None)
    assert cell is not None, "Номерная ячейка не создана"
    assert cell.tag == "mxCell"
    assert "style" in cell.attrib
    assert "value" in cell.attrib
    assert "html=1" in cell.attrib["style"]
    assert cell.attrib["value"].startswith('<font'), "HTML должен быть в value"


def test_preprocessing_image_adds_cells(design):
    design.preprocessing_image(index=0, width=320, height=270, position_x=10, position_y=20)

    image_cells = [e for e in design._xml_root if e.attrib.get("style", "").startswith("shape=image")]
    assert len(image_cells) == 1, "Изображение не добавлено"

    mx = image_cells[0].find("mxGeometry")
    assert mx is not None, "mxGeometry отсутствует"
    assert mx.attrib["x"] == "10"
    assert mx.attrib["y"] == "20"


def test_generate_id_format():
    id_ = DrawioImageDesign._generate_id()
    assert id_.startswith("E__")
    assert id_.endswith("-1")
