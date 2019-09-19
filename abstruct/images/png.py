'''
# Portable Network Graphics

Format created to replace patent-emcumbered GIF files.

The specification is at <http://www.libpng.org/pub/png/spec/1.2/PNG-Contents.html>.

'''
from enum import Enum

from abstruct.core import Chunk
from abstruct import (
    fields,
)
from abstruct.properties import Dependency, RatioDependency
from abstruct.common import crc


class PNGColorType(Enum):
    '''The color type definition of the PNG is a little tricky and doesn't seem
    to follow a bit-mask. We are going to list all the valid cases.'''
    GRAYSCALE = 0x00
    RGB       = 0x02
    RGB_PALETTE = 0x03
    GS_ALPHA    = 0x04
    RGBA        = 0x06


class PNGCompressionType(Enum):
    '''There is only one method of compression'''
    DEFLATE = 0x00


class PNGFilterType(Enum):
    NONE = 0x00
    SUB  = 0x01
    UP   = 0x02
    AVG  = 0x03
    PAETH = 0x04


class IHDRData(Chunk):
    '''
    Width and height give the image dimensions in pixels.
    Bit depth is a single-byte integer giving the number of bits per sample or per palette index (not per pixel).
    Color type is a single-byte integer that describes the interpretation of the image data.
    '''
    width       = fields.StructField('I', little_endian=False)
    height      = fields.StructField('I', little_endian=False)
    depth       = fields.StructField('B')
    color       = fields.StructField('B', enum=PNGColorType, default=PNGColorType.GRAYSCALE)
    compression = fields.StructField('B', enum=PNGCompressionType, default=PNGCompressionType.DEFLATE)
    filter      = fields.StructField('B', enum=PNGFilterType, default=PNGFilterType.NONE)
    interlace   = fields.StructField('B')

    def __str__(self):
        return '%dx%dx%d' % (
            self.width.value,
            self.height.value,
            self.depth.value,
        )


class PLTEEntry(Chunk):
    red   = fields.StructField('B')
    green = fields.StructField('B')
    blue  = fields.StructField('B')


class PNGHeader(Chunk):
    magic = fields.StringField(8, default=b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a')


type2field = {
    b'IHDR': IHDRData(),
    b'PLTE': fields.RealArrayField(PLTEEntry, n=RatioDependency(3, '.length')),
    b'gAMA': fields.RealStringField(Dependency('.length')),
    fields.RealSelectField.Type.DEFAULT: fields.RealStringField(Dependency('.length')),
}


class PNGChunk(Chunk):
    '''
    This is the main data structure of the format: the 4 fields represent
    a chunk into the file. Each field is intended big-endian.

    A chunk is defined as critical or ancillary depending on the case of the
    starting letter of the type field.

    The crc field is network-byte-order CRC-32 computed over the chunk type and chunk data, but not the length.

    # Critical chunks

     1. IHDR: contains image's width, height, bit depth, color type, compression method, filter method and interlace method
     2. PLTE: contains the palette data
     3. IDAT: contains the actual image data (compressed)
     4. IEND: is the terminator chunk
    '''
    length = fields.StructField('I', little_endian=False) # big endian
    type   = fields.StringField(4)
    Data   = fields.SelectField('type', type2field)
    crc    = crc.CRCField(['type', 'Data'], little_endian=False) # network byte order

    def isCritical(self):
        return chr(self.type.value[0]).isupper()


class PNGFile(Chunk):
    header = fields.PNGHeaderField()
    chunks = fields.ArrayField(PNGChunk, canary=lambda x:x.type.value == b'IEND')

