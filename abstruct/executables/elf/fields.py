'''
# Elf format

Executable and Linkage Format is a file format vastly used in the *nix world.

'''
from enum import Enum

from ... import fields
from ...core import Chunk
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
    EI_MAG0 = fields.StructField('c', default=b'\x7f')
    EI_MAG1 = fields.StructField('c', default=b'E')
    EI_MAG2    = fields.StructField('c', default=b'L')
    EI_MAG3    = fields.StructField('c', default=b'F')
    EI_CLASS   = fields.StructField('B', default=ElfEIClass.ELFCLASS32.value) # determines the architecture
    EI_DATA    = fields.StructField('B', default=ElfEIData.ELFDATA2LSB.value) # determines the endianess of the binary data
    EI_VERSION = fields.StructField('B', default=1) # always 1
    EI_PAD     = fields.StringField(9)


class ElfSegmentType(Enum):
    PT_NULL = 0
    PT_LOAD = 1
    PT_DYNAMIC = 2
    PT_INTERP  = 3
    PT_NOTE    = 4
    PT_SHLIB   = 5
    PT_PHDR    = 6
    PT_LOPROC  = 0x70000000
    PT_HIPROC  = 0x7fffffff


class RealElf32_Addr(fields.StructField):
    def __init__(self, **kwargs):
        super().__init__('<I')
