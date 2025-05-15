import pytest
from PIL import Image
from pathlib import Path
from image_processing.imageDesign import ImagesDesign
from image_processing.enumerates import LayoutMode, SignaturePosition, LabelMode

import os
import shutil

test_img_path = Path("./test/test_images")
test_img_path.mkdir(exist_ok=True)

# Create dummy images for testing
for i in range(4):
    img = Image.new("RGB", (100, 100), color=(i*50, i*50, i*50))
    img.save(test_img_path / f"img_{i}.png")

def cleanup():
    shutil.rmtree(test_img_path)

@pytest.fixture(scope="module")
def image_design():
    yield ImagesDesign(
        images_path=test_img_path,
        border_size=5,
        border_fill="blue",
        signature=True,
        signature_label=LabelMode.ROMAN,
        signature_pos=SignaturePosition.BOTTOM_RIGHT,
        signature_size=(30, 30),
        signature_color="red",
        signature_font_size=16,
        draw_axis=True,
        axis_labels=("X", "Y"),
        axis_offset=(10, 10),
        axis_length=30,
        axis_width=2,
        font_family="./fonts/Arial.ttf",
        axis_font_size=12
    )
    cleanup()

def test_len(image_design):
    assert len(image_design) == 4

def test_get_item(image_design):
    assert isinstance(image_design[0], Image.Image)

def test_set_item(image_design):
    new_img = Image.new("RGB", (100, 100), color="green")
    image_design[1] = new_img
    assert image_design[1] == new_img

def test_del_item(image_design):
    initial = len(image_design)
    del image_design[0]
    assert len(image_design) == initial - 1

def test_contains(image_design):
    img = image_design[0]
    assert img in image_design

def test_iter(image_design):
    for img in image_design:
        assert isinstance(img, Image.Image)

def test_united_images_row(image_design):
    img = image_design.united_images(layout="row")
    assert isinstance(img, Image.Image)

def test_united_images_column(image_design):
    img = image_design.united_images(layout=LayoutMode.COLUMN)
    assert isinstance(img, Image.Image)

def test_united_images_grid(image_design):
    img = image_design.united_images(layout="grid")
    assert isinstance(img, Image.Image)

def test_append(image_design):
    initial_len = len(image_design)
    new_img = Image.new("RGB", (100, 100), color="yellow")
    image_design.append(new_img)
    assert len(image_design) == initial_len + 1

def test_invalid_signature_label():
    with pytest.raises(TypeError):
        ImagesDesign(images_path=test_img_path, signature_label=123)

def test_invalid_layout(image_design):
    with pytest.raises(ValueError):
        image_design.united_images(layout="diagonal")

def test_signature_label_modes():
    design = ImagesDesign(images_path=test_img_path, signature_label="roman")
    img = design.united_images()
    assert isinstance(img, Image.Image)

def test_axis_offset_tuple():
    design = ImagesDesign(images_path=test_img_path, axis_offset=(20, 40))
    img = design.united_images()
    assert isinstance(img, Image.Image)


def test_repr_and_str(image_design):
    assert isinstance(repr(image_design), str)
    assert isinstance(str(image_design), str)

def test_signature_label_as_tuple():
    labels = ("One", "Two", "Three", "Four")
    design = ImagesDesign(images_path=test_img_path, signature_label=labels)
    img = design.united_images()
    assert isinstance(img, Image.Image)

def test_signature_label_single_string():
    design = ImagesDesign(images_path=test_img_path, signature_label="Fixed")
    img = design.united_images()
    assert isinstance(img, Image.Image)


def test_validate_border_size():
    from image_processing.imageDesign import ImagesDesign as ID
    assert ID._validate_border_size(10) == (10, 10, 10, 10)
    assert ID._validate_border_size((1, 2, 3, 4)) == (1, 2, 3, 4)
    with pytest.raises(TypeError):
        ID._validate_border_size("invalid")


def test_validate_color():
    from image_processing.imageDesign import ImagesDesign as ID
    assert ID._validate_color("blue") == "blue"
    assert ID._validate_color((10, 20, 30)) == (10, 20, 30)
    with pytest.raises(TypeError):
        ID._validate_color([255, 255, 255])


def test_validate_tuple_pair():
    from image_processing.imageDesign import ImagesDesign as ID
    assert ID._validate_tuple_pair((1, 2), "test") == (1, 2)
    with pytest.raises(TypeError):
        ID._validate_tuple_pair((1,), "test")
