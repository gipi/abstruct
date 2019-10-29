from enum import Enum
from ...core import Chunk
from ... import fields
from .fields import Elf_Addr, ElfRelocationInfoField


class ElfRelEntry(Chunk):
    r_offset = Elf_Addr()
    r_info   = ElfRelocationInfoField()


class ElfRelocationTable(fields.RealArrayField):

    def __init__(self, *args, size=None, **kwargs):
        if size and 'n' in kwargs:  # FIXME: factorize into RealArrayField
            raise ValueError('you cannot pass both n and size')

        if size:
            kwargs['n'] = int(size / ElfRelEntry(father=kwargs['father']).size())

        super().__init__(ElfRelEntry, *args, **kwargs)


class ElfRelocationType_i386(Enum):
    R_386_NONE = 0
    R_386_32   = 1
    R_386_PC32 = 2
    R_386_GOT32 = 3
    R_386_PLT32 = 4
    R_386_COPY  = 5
    R_386_GLOB_DAT = 6
    R_386_JMP_SLOT = 7
    R_386_RELATIVE = 8
    R_386_GOTOFF   = 9
    R_386_GOTPC    = 10
    R_386_32PLT    = 11
    R_386_16       = 20
    R_386_PC16     = 21
    R_386_8        = 22
    R_386_PC8      = 23
    R_386_SIZE32   = 38
