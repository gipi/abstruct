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
    NONE                    = 0
    ENCRIPTED               = 1 << 0
    COMPRESSION_OPTIONLSB   = 1 << 1
    COMPRESSION_OPTIONMSB   = 1 << 2
    DATA_DESCRIPTOR         = 1 << 3
    ENHANCED_DEFLATION      = 1 << 4
    COMPRESSED_PATCHED_DATA = 1 << 5
    STRONG_ENCRYPTION       = 1 << 6
    # from 7th to 10th are not used
    LANGUAGE_ENCODING       = 1 << 11
    MASK_HEADER             = 1 << 13


class ZIPCompressionMethod(Flag):
    NONE                = 0
    SHRUNK              = 1
    REDUCED_FACTOR_1    = 2
    REDUCED_FACTOR_2    = 3
    REDUCED_FACTOR_3    = 4
    REDUCED_FACTOR_4    = 5
    IMPLODED            = 6
    RESERVED            = 7
    DEFLATED            = 8
    ENCHANCED_DEFLATED  = 9
    PKWARE_DCL_IMPLODED = 10
    BZIP2               = 12
    LZMA                = 14
    IBM_TERSE           = 18
    IBM_LZ77            = 19
    PPMd                = 98


class ZIPHeader(Chunk):
    signature         = fields.StringField(0x4, default=b'PK\x03\x04')
    version           = fields.StructField('H')
    flags             = fields.StructField('H', enum=ZIPFlags)
    compression       = fields.StructField('H', enum=ZIPCompressionMethod)
    modification_time = fields.StructField('H')  # TODO: MS DOS field
    modification_date = fields.StructField('H')
    crc32             = fields.StructField('I')  # TODO: CRC32 depending on data from file content
    compressed_size   = fields.StructField('I')
    uncompressed_size = fields.StructField('I')
    filename_length   = fields.StructField('H')
    extra_length      = fields.StructField('H')
    filename          = fields.StringField(Dependency('filename_length'))
    extra_field       = fields.StringField(Dependency('extra_length'))
