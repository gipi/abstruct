from abstruct.images.png import PNGHeader, PNGFile, PNGColorType


def test_header(self):
    """Check header is right"""
    png_header = PNGHeader()

    self.assertEqual(png_header.magic.value, b'\x89PNG\x0d\x0a\x1a\x0a')


def test_png_file(test_root_dir):
    """Check unpacking a pre-established PNG file is fine"""
    path_png = str(test_root_dir / '..' / 'extra' / 'png' / 'red.png')

    png = PNGFile(path_png)

    assert png.chunks.value[0].type.value == b'IHDR'
    assert png.chunks.value[0].Data._field.color.value == PNGColorType.RGB_PALETTE

    for idx, chunk in enumerate(png.chunks.value):
        print(idx, chunk, chunk.isCritical(), chunk.crc.calculate())
