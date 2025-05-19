from pathlib import Path
import shutil

from PIL import Image
import pytest

from science_helper.image_processing.enumerates import (
    LabelMode,
    LayoutMode,
    SignaturePosition,
)
from science_helper.image_processing.image_design import ImagesDesign


test_img_path = Path("./test/test_images")
test_img_path.mkdir(exist_ok=True)


for i in range(4):
    img = Image.new("RGB", (100, 100), color=(i * 50, i * 50, i * 50))
    img.save(test_img_path / f"img_{i}.png")


def cleanup():  # noqa: D103
    shutil.rmtree(test_img_path)


@pytest.fixture(scope="module")
def image_design():  # noqa: D103
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
        axis_font_size=12,
    )
    cleanup()


def test_len(image_design):  # noqa: D103
    expected_image = 4
    assert len(image_design) == expected_image


def test_get_item(image_design):  # noqa: D103
    assert isinstance(image_design[0], Image.Image)


def test_set_item(image_design):  # noqa: D103
    new_img = Image.new("RGB", (100, 100), color="green")
    image_design[1] = new_img
    assert image_design[1] == new_img


def test_del_item(image_design):  # noqa: D103
    initial = len(image_design)
    del image_design[0]
    assert len(image_design) == initial - 1


def test_contains(image_design):  # noqa: D103
    img = image_design[0]
    assert img in image_design


def test_iter(image_design):  # noqa: D103
    for img in image_design:
        assert isinstance(img, Image.Image)


def test_united_images_row(image_design):  # noqa: D103
    img = image_design.united_images(layout="row")
    assert isinstance(img, Image.Image)


def test_united_images_column(image_design):  # noqa: D103
    img = image_design.united_images(layout=LayoutMode.COLUMN)
    assert isinstance(img, Image.Image)


def test_united_images_grid(image_design):  # noqa: D103
    img = image_design.united_images(layout="grid")
    assert isinstance(img, Image.Image)


def test_append(image_design):  # noqa: D103
    initial_len = len(image_design)
    new_img = Image.new("RGB", (100, 100), color="yellow")
    image_design.append(new_img)
    assert len(image_design) == initial_len + 1


def test_invalid_signature_label():  # noqa: D103
    with pytest.raises(TypeError):
        ImagesDesign(images_path=test_img_path, signature_label=123)


def test_invalid_layout(image_design):  # noqa: D103
    with pytest.raises(ValueError):
        image_design.united_images(layout="diagonal")


def test_signature_label_modes():  # noqa: D103
    design = ImagesDesign(images_path=test_img_path, signature_label="roman")
    img = design.united_images()
    assert isinstance(img, Image.Image)


def test_axis_offset_tuple():  # noqa: D103
    design = ImagesDesign(images_path=test_img_path, axis_offset=(20, 40))
    img = design.united_images()
    assert isinstance(img, Image.Image)


def test_repr_and_str(image_design):  # noqa: D103
    assert isinstance(repr(image_design), str)
    assert isinstance(str(image_design), str)


def test_signature_label_as_tuple():  # noqa: D103
    labels = ("One", "Two", "Three", "Four")
    design = ImagesDesign(images_path=test_img_path, signature_label=labels)
    img = design.united_images()
    assert isinstance(img, Image.Image)


def test_signature_label_single_string():  # noqa: D103
    design = ImagesDesign(images_path=test_img_path, signature_label="Fixed")
    img = design.united_images()
    assert isinstance(img, Image.Image)


def test_validate_border_size():  # noqa: D103
    assert ImagesDesign._validate_border_size(10) == (10, 10, 10, 10)
    assert ImagesDesign._validate_border_size((1, 2, 3, 4)) == (1, 2, 3, 4)
    with pytest.raises(TypeError):
        ImagesDesign._validate_border_size("invalid")


def test_validate_color():  # noqa: D103
    assert ImagesDesign._validate_color("blue") == "blue"
    assert ImagesDesign._validate_color((10, 20, 30)) == (10, 20, 30)
    with pytest.raises(TypeError):
        ImagesDesign._validate_color([255, 255, 255])


def test_validate_tuple_pair():  # noqa: D103
    assert ImagesDesign._validate_tuple_pair((1, 2), "test") == (1, 2)
    with pytest.raises(TypeError):
        ImagesDesign._validate_tuple_pair((1,), "test")
