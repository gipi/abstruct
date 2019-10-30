#!/usr/bin/env python3
'''
 $ convert -size 5x5 xc:red -size 5x5 xc:green -append show:
'''
import logging
import sys
import os
import numpy as np
from PIL import Image

from abstruct.images.png import (
    PNGFile,
    PNGColorType,
)
from abstruct.images.png.utils import *


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO if 'DEBUG' not in os.environ else logging.DEBUG)


def usage(progname):
    print(f'usage: {progname} <png file path>')
    sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        usage(sys.argv[0])

    filepath = sys.argv[1]

    png = PNGFile(filepath)

    for idx, chunk in enumerate(png.chunks.value):
        print(f'[{idx:02d}] {chunk!r}')

    header  = get_chunk_by_name(png.chunks.value, 'IHDR').Data._field

    if header.color.value != PNGColorType.RGB_PALETTE:
        raise ValueError(f'Color type {header.color.value!r} not supported')

    palette = get_chunk_by_name(png.chunks.value, 'PLTE').Data._field.value
    data    = get_IDAT_data(png.chunks.value)
    matrix = [pixels_from_image_data(ft, id, palette) for ft, id in iter_scanline(header.width.value, header.depth.value, data, palette)]

    pixels = np.array(matrix, dtype=np.uint8)

    image = Image.fromarray(pixels, 'RGB')
    image.show()
