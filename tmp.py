import rawpy
import imageio

import skimage
from skimage import data, io, filters
from pathlib import Path

from PIL import Image, ImageFilter
from photogrammetry_service import ext_tool_adaptor, img_util


def dng_to_png():
    p = '/Users/duyyudus/Git/photogrammetry-service/sample_data/task4/2_DNG/DSC05669.dng'
    p2 = '/Users/duyyudus/Git/photogrammetry-service/sample_data/task4/2_DNG/DSC05669.png'
    with rawpy.imread(p) as raw:
        rgb = raw.postprocess(
            highlight_mode=0, no_auto_bright=False, use_camera_wb=True, gamma=(2.4, 12.92)
        )
    imageio.imsave(p2, rgb)


def blur():
    p = '/Users/duyyudus/Git/photogrammetry-service/sample_data/task4/2_DNG/DSC05669.png'
    # p = '/Users/duyyudus/Git/photogrammetry-service/img.png'
    p2 = '/Users/duyyudus/Git/photogrammetry-service/sample_data/task4/2_DNG/DSC05669_blur.png'
    # p2 = '/Users/duyyudus/Git/photogrammetry-service/blur.png'

    image = skimage.io.imread(fname=p, plugin='pil')
    blurred = skimage.filters.gaussian(image, sigma=(50, 50), truncate=3.5, multichannel=True)
    # viewer = ImageViewer(blurred)
    # viewer.show()
    skimage.io.imsave(p2, blurred)


def png_to_tif():
    p = '/Users/duyyudus/Git/photogrammetry-service/sample_data/task4/2_DNG/DSC05669_blur.png'
    p2 = '/Users/duyyudus/Git/photogrammetry-service/sample_data/task4/2_DNG/DSC05669_blur.tif'
    im = Image.open(p)
    im.save(p2)


# dng_to_png()
# blur()
# png_to_tif()

# ext_tool_adaptor.run_dng_conversion(
#     Path('/Users/duyyudus/Git/photogrammetry-service/sample_data/task5/cache/color_checker.ARW'),
#     Path('/Users/duyyudus/Git/photogrammetry-service/sample_data/task5/cache'),
#     Path('/Applications/Adobe DNG Converter.app/Contents/MacOS/Adobe DNG Converter'),
# )

swatch = img_util.compute_swatch(
    Path(
        '/Users/duyyudus/Git/photogrammetry-service/sample_data/task5/cache/color_checker_blur.tiff'
    )
)
img_util.color_correct(
    Path('/Users/duyyudus/Git/photogrammetry-service/sample_data/task5/2_DNG/DSC05670.dng'),
    Path(
        '/Users/duyyudus/Git/photogrammetry-service/sample_data/task5/3_COLOR_CORRECTED/DSC05670.jpg'
    ),
    swatch,
)
