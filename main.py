from image_processing import ImagesDesign, LabelMode, LayoutMode, SignaturePosition


if __name__ == "__main__":
    design = ImagesDesign(images_path="./images",
                          border_size=10,
                          signature=True,
                          signature_label=LabelMode.ROMAN,
                          signature_pos=SignaturePosition.TOP_LEFT,
                          signature_size=(40, 40),
                          signature_color="black",
                          signature_font_size=18,
                          draw_axis=True,
                          axis_labels=(("t", "t", "t", "t"), ("f(x)", "f(y)", "Y(x)", "Z(y)")),
                          axis_offset=25,
                          axis_length=60,
                          axis_width=3,
                          font_family="./fonts/Roboto.ttf",
                          axis_font_size=18)
    img = design.united_images(LayoutMode.GRID, width=320, height=280)
    # img = design.preprocessing_image(2, width=320, height=280)
    img.show()
    