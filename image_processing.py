import math
from enum import Enum
from PIL import Image
from pathlib import Path
from typing import List, Optional
from image_processing import ISOPage, PageSeries, Orientation, ColorMode, LayoutMode






    

img = ISOPage(series=PageSeries.A, 
              number=9, 
              dpi=600,
              orientation=Orientation.PORTRAIT,
              color_mode=ColorMode.RGB)


im = img.place_images(image_paths=["./images/1.png",
                                   "./images/2.png",
                                   "./images/3.png",
                                   "./images/4.png"],
                      margin=20,
                      layout=LayoutMode.GRID)

im.show()