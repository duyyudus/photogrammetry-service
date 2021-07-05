"""
Image processing utilities
"""

import os
from pathlib import Path

import colour
import imageio
import rawpy
import skimage
from colour_checker_detection import detect_colour_checkers_segmentation
from colour_checker_detection.detection.segmentation import ColourCheckerSwatchesData

from PIL import Image
from skimage import data, filters, io

D65 = colour.CCS_ILLUMINANTS['CIE 1931 2 Degree Standard Observer']['D65']
REF_COLOUR_CHECKER = colour.CCS_COLOURCHECKERS['ColorChecker24 - After November 2014']
REF_SWATCHES = colour.XYZ_to_RGB(
    colour.xyY_to_XYZ(list(REF_COLOUR_CHECKER.data.values())),
    REF_COLOUR_CHECKER.illuminant,
    D65,
    colour.RGB_COLOURSPACES['sRGB'].matrix_XYZ_to_RGB,
)


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


def verify_color_swatches(swatches):
    deviation = []
    rgb_RCCL = colour.XYZ_to_RGB(
        colour.xyY_to_XYZ(list(REF_COLOUR_CHECKER.data.values())),
        D65,
        D65,
        colour.RGB_COLOURSPACES['sRGB'].matrix_XYZ_to_RGB,
    )
    for swatch in swatches:
        swatch_cc = colour.colour_correction(swatch, swatch, REF_SWATCHES)
        CCL = swatch_cc
        totalsum = 0.0
        for i in range(len(rgb_RCCL)):
            totalsum += (
                abs(rgb_RCCL[i][0] - CCL[i][0])
                + abs(rgb_RCCL[i][1] - CCL[i][1])
                + abs(rgb_RCCL[i][2] - CCL[i][2])
            )
        deviation.append(totalsum)
    print("swatches deviations: " + str(deviation))
    min_d = 100.0
    min_i = -1
    for i in range(len(deviation)):
        if deviation[i] < min_d:
            min_d = deviation[i]
            min_i = i
    print("The lowest devi is: " + str(min_d))
    result = False
    if min_d < 3.0:
        print("devi is near good ! ")
        result = True
    elif min_d < 5.0:
        print("devi is near average ! ")
        result = True
    elif min_d < 8.0:
        print("devi is near BAD ! the COLORS will be off!!!!")
        result = True
    else:
        print("devi is BAD ! the Swatches are completely off!!!!")
        result = False
    return result, swatches[min_i]


def compute_swatch(color_checker: Path) -> ColourCheckerSwatchesData:
    """
    Args:
        color_checker (Path): blurry TIFF color checker
    """
    color_checker_img = colour.cctf_decoding(colour.io.read_image(color_checker.as_posix()))
    swatches = detect_colour_checkers_segmentation(color_checker_img)
    vresult, swatch = verify_color_swatches(swatches)
    return swatch


def color_correct(src: Path, tg: Path, swatch: ColourCheckerSwatchesData, cache_dir: Path = None):
    """
    Args:
        src (Path): DNG image
        tg (Path): JPG image
    """

    cache_dir = cache_dir if cache_dir else tg.parent

    # Convert source image to temp TIFF
    tmp_tif = cache_dir.joinpath(f'{tg.stem}_tmp.tiff')
    dng_to_tif(src, tmp_tif)

    # Correct color of that temp TIFF
    image = colour.cctf_decoding(colour.io.read_image(tmp_tif.as_posix()))
    cc_image = colour.colour_correction(image, swatch, REF_SWATCHES, 'Finlayson 2015')
    cc_tmp_tif = cache_dir.joinpath(f'{tg.stem}_cc.tiff')
    colour.io.write_image(colour.cctf_encoding(cc_image), cc_tmp_tif.as_posix(), bit_depth='uint8')

    # Save color corrected TIFF as JPG
    final_cc_jpg = tg.parent.joinpath(f'{tg.stem}.jpg')
    img = Image.open(cc_tmp_tif.as_posix())
    img.save(final_cc_jpg.as_posix(), quality=95, subsampling=0)

    # Clean tmp files
    os.remove(tmp_tif.as_posix())
    os.remove(cc_tmp_tif.as_posix())
