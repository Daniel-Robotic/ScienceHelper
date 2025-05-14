from image_processing import ImagesDesign, LabelMode, LayoutMode, SignaturePosition


if __name__ == "__main__":
    design = ImagesDesign(images_path="./images",
                          border_size=0,
                          signature=True,
                          signature_label="x",
                          signature_pos=SignaturePosition.TOP_LEFT,
                          signature_size=(100, 100),
                          signature_color="black",
                          signature_font_size=50,
                          draw_axis=True,
                          axis_labels=(("t", "t", "t", "t"), ("f(x)", "f(y)", "Y(x)", "Z(y)")),
                          axis_offset=(20, 60),
                          axis_length=240,
                          axis_width=5,
                          font_family="./fonts/Roboto.ttf",
                          axis_font_size=24)
    img = design.united_images(LayoutMode.GRID, grid_cols=3, grid_rows=1)
    img.show()
    