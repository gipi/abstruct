'''
# PKZIP format

The general structure is the following
  .---------------------------------.
  | file header                     |
  | central directory file header 1 |
  | central directory file header 2 |
  | central directory file header 3 |
    ...
  | central directory file header N |
  | end of central directory        |
  '---------------------------------'

This format can be splitted in multiple medium (historically using floppy).

'''
from enum import Flag
from ..core import Chunk
from .. import fields
from ..properties import Dependency


class ZIPFlags(Flag):
    ENCRIPTED = 0
    COMPRESSION_OPTIONLSB = 1 << 1
    COMPRESSION_OPTIONMSB = 1 << 2
    DATA_DESCRIPTOR = 1 << 3
    ENHANCED_DEFLATION = 1 << 4
    COMPRESSED_PATCHED_DATA = 1 << 5



class ZIPHeader(Chunk):
    signature         = fields.StringField(0x4, default=b'PK\x03\x04')
    version           = fields.StructField('H')
    flags             = fields.BitField(ZIPFlags, 'H')
    compression       = fields.StructField('H')
    modification_time = fields.StructField('H') # TODO: MS DOS field
    modification_date = fields.StructField('H')
    crc32             = fields.StructField('I') # TODO: CRC32 depending on data from file content
    compressed_size   = fields.StructField('I')
    uncompressed_size = fields.StructField('I')
    filename_length   = fields.StructField('H')
    extra_length      = fields.StructField('H')
    filename          = fields.StringField(Dependency('filename_length'))
    extra_field       = fields.StringField(Dependency('extra_length'))

