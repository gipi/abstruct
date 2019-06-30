'''
# Portable Network Graphics

Format created to replace patent-emcumbered GIF files.

The specification is at <http://www.libpng.org/pub/png/spec/1.2/PNG-Contents.html>.

'''
from abstruct.core import Chunk
from abstruct import fields
from abstruct.properties import Dependency


class PNGHeader(Chunk):
    magic = fields.StringField(8, default=b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a')


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
    data   = fields.StringField(Dependency('length'))
    crc    = fields.StructField('I', formatter='%08x') # network byte order

    def isCritical(self):
        return chr(self.type.value[0]).isupper()


class IHDRData(Chunk):
    width = fields.StructField('I', little_endian=False)
    height = fields.StructField('I', little_endian=False)
    depth = fields.StructField('c')
    color = fields.StructField('c')
    compression = fields.StructField('c')
    filter = fields.StructField('c')
    interlace = fields.StructField('c')


class PLTEEntry(Chunk):
    red   = fields.StructField('c')
    green = fields.StructField('c')
    blue  = fields.StructField('c')


class PLTEData(Chunk):
    palettes = fields.ArrayField(PLTEEntry)


class PNGFile(Chunk):
    header = fields.PNGHeaderField()
    chunks = fields.ArrayField(PNGChunk)

