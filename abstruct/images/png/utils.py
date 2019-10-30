import logging


logger = logging.getLogger(__name__)


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


def get_IDAT_data(chunks):
    '''In a PNG file, the concatenation of the contents of all the IDAT chunks makes up a zlib datastream,
    the boundaries between IDAT chunks are arbitrary and can fall anywhere in the zlib datastream.
    '''
    chunks = list(filter(lambda x: x.type.value.decode() == 'IDAT', chunks))

    data = b''

    for chunk in chunks:
        data += chunk.Data._field.value

    import zlib

    return zlib.decompress(data)
