"""
Image processing utilities
"""

from os import path
from pathlib import Path

import imageio
import rawpy
import skimage
from PIL import Image
from skimage import data, filters, io


def dng_to_png(src: Path, tg: Path):
    with rawpy.imread(src.as_posix()) as raw:
        rgb = raw.postprocess(
            highlight_mode=0, no_auto_bright=False, use_camera_wb=True, gamma=(2.4, 12.92)
        )
    imageio.imsave(tg.as_posix(), rgb)


def dng_to_tif(src: Path, tg: Path):
    with rawpy.imread(src.as_posix()) as raw:
        rgb = raw.postprocess(
            highlight_mode=0, no_auto_bright=True, use_camera_wb=True, gamma=(2.4, 12.92)
        )
    imageio.imsave(tg.as_posix(), rgb)


def blur(src: Path, tg: Path):
    """Blur image
    WARNING: does not work with TIFF
    """
    image = skimage.io.imread(fname=src.as_posix(), plugin='pil')
    blurred = skimage.filters.gaussian(image, sigma=(10, 10), truncate=3.5, multichannel=True)
    skimage.io.imsave(tg.as_posix(), blurred)


def png_to_tif(src: Path, tg: Path):
    im = Image.open(src.as_posix())
    im.save(tg.as_posix())
