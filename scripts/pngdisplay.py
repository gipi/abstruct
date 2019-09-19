'''
 $ convert -size 5x5 xc:red -size 5x5 xc:green -append show:
'''
import sys
import numpy as np
from matplotlib import pyplot as plt

from abstruct.images.png import (
    PNGFile,
)


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

    pixels = [BitArray(pixels)[_:_ + 2].int for _ in range(0, len(pixels) * 8, 2)]

    return filter_type, pixels[:width]


def iter_scanline(width, depth, idata, palette):
    import math

    # calculate the number of byte for scanline
    # the scanline starts always at byte boundary
    # moreover has one byte for the filter type
    n_byte_scanline = math.ceil(width * depth / 8) + 1

    for scanline in iter_scanline_bits(idata, n_byte_scanline):
        ft, image_data = get_scanline_data(scanline, width, depth)
        yield ft, image_data


def pixels_from_image_data(ft, image_data, palette):
    return [palette[_].pixel for _ in image_data]


if __name__ == '__main__':
    if len(sys.argv) < 2:
        usage(sys.argv[0])

    filepath = sys.argv[1]

    png = PNGFile(filepath)

    for idx, chunk in enumerate(png.chunks.value):
        print(f'[{idx:02d}] {chunk!r}')

    header = png.chunks.value[0].Data._field
    palette = png.chunks.value[3].Data._field.value
    data = png.chunks.value[7].Data._field.value
    matrix = [pixels_from_image_data(ft, id, palette) for ft, id in iter_scanline(header.width.value, header.depth.value, data, palette)]

    pixels = np.array(matrix, dtype=np.uint8)

    plt.imshow(pixels)
    plt.show()

    import ipdb
    ipdb.set_trace()
