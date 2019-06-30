from abstruct.core import Chunk
from abstruct import fields
from abstruct.properties import Dependency


class PNGHeader(Chunk):
    magic = fields.StringField(8, default=b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a')


class PNGChunk(Chunk):
    length = fields.StructField('I', little_endian=False) # big endian
    type   = fields.StringField(4)
    data   = fields.StringField(Dependency('length'))
    crc    = fields.StructField('I') # network byte order

class PNGFile(Chunk):
    header = fields.PNGHeaderField()
    chunks = fields.ArrayField(PNGChunk)

