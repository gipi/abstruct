import sys

from abstruct.images.png import (
    PNGFile,
)


def usage(progname):
    print(f'usage: {progname} <png file path>')
    sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        usage(sys.argv[0])

    filepath = sys.argv[1]

    png = PNGFile(filepath)

    print(repr(png.chunks.value[0].Data._field))

    for idx, chunk in enumerate(png.chunks.value):
        print(f'[{idx:02d}] {chunk!r}')
