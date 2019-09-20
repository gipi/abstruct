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
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO if 'DEBUG' not in os.environ else logging.DEBUG)


def usage(progname):
    print(f'usage: {progname} <png file path>')
    sys.exit(1)


def iter_scanline_bits(idata, n):
    for idx in range(0, len(idata), n):
        yield idata[idx:idx + n]


def get_scanline_data(scanline, width, depth):
    from bitstring import BitArray
    filter_type = scanline[:1]
    pixels = scanline[1:]

    pixels = [BitArray(pixels)[_:_ + depth].uint for _ in range(0, len(pixels) * 8, depth)]

    return filter_type, pixels[:width]


def iter_scanline(width, depth, idata, palette):
    import math

    # calculate the number of byte for scanline
    # the scanline starts always at byte boundary
    # moreover has one byte for the filter type
    n_byte_scanline = math.ceil(width * depth / 8) + 1

    logger.debug(f'iterating over scanlines for width {width} and depth {depth}')
    for scanline in iter_scanline_bits(idata, n_byte_scanline):
        ft, image_data = get_scanline_data(scanline, width, depth)

        logger.debug(f'scanline: {ft} {image_data}')
        if ft != b'\x00':
            raise ValueError(f'Filter type {ft!r} not implemented')
        yield ft, image_data


def pixels_from_image_data(ft, image_data, palette):
    return [palette[_].pixel for _ in image_data]


def get_chunk_by_name(chunks, name):
    chunk = list(filter(lambda x: x.type.value.decode() == name, chunks))

    if len(chunk) == 0:
        raise ValueError(f'no chunk with name {name}')

    return chunk if len(chunk) > 1 else chunk[0]


if __name__ == '__main__':
    if len(sys.argv) < 2:
        usage(sys.argv[0])

    filepath = sys.argv[1]

    png = PNGFile(filepath)

    for idx, chunk in enumerate(png.chunks.value):
        print(f'[{idx:02d}] {chunk!r}')

    header  = get_chunk_by_name(png.chunks.value, 'IHDR').Data._field
    palette = get_chunk_by_name(png.chunks.value, 'PLTE').Data._field.value
    data    = get_chunk_by_name(png.chunks.value, 'IDAT').Data._field.value
    matrix = [pixels_from_image_data(ft, id, palette) for ft, id in iter_scanline(header.width.value, header.depth.value, data, palette)]

    pixels = np.array(matrix, dtype=np.uint8)

    image = Image.fromarray(pixels, 'RGB')
    image.show()
