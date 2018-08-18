from enum import Enum

from .. import fields
from ..core import Chunk
"""
From ELF: Executable and Linkable Format page 8, Data types


"""


# FIXME: the endianess depens on EI_DATA

class ElfEIClass(Enum):
    ELFCLASSNONE = 0
    ELFCLASS32   = 1
    ELFCLASS64   = 2


class ElfEIData(Enum):
    ELFDATANONE = 0
    ELFDATA2LSB = 1
    ELFDATA2MSB = 2


class ElfIdent(Chunk):
    EI_MAG0 = fields.StructField('c')
    EI_MAG1 = fields.StructField('c')
    EI_MAG2    = fields.StructField('c')
    EI_MAG3    = fields.StructField('c')
    EI_CLASS   = fields.StructField('B')
    EI_DATA    = fields.StructField('B')
    EI_VERSION = fields.StructField('B')
    EI_PAD     = fields.StringField(9)


class RealElf32_Addr(fields.StructField):
    def __init__(self, **kwargs):
        super().__init__('<I')
