'''
# Portable Network Graphics

Format created to replace patent-emcumbered GIF files.

'''
from abstruct.core import Chunk
from abstruct import fields
from abstruct.properties import Dependency


class PNGHeader(Chunk):
    magic = fields.StringField(8, default=b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a')


class PNGChunk(Chunk):
    '''
    This is the main data structure of the format: the 4 fields represent
    a chunk into the file.

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


class PNGFile(Chunk):
    header = fields.PNGHeaderField()
    chunks = fields.ArrayField(PNGChunk)

