from enum import Enum

from ..core import Chunk, Dependency
from .fields import *
from .. import fields
from ..properties import Offset


class ElfType(Enum):
    ET_NONE = 0
    ET_REL  = 1
    ET_EXEC = 2
    ET_DYN  = 3
    ET_CORE = 4
    ET_LOPROC = 0xff00
    ET_HIPROC = 0xffff


class ElfMachine(Enum):
    EM_NONE  = 0
    EM_M32   = 1
    EM_SPARC = 2
    EM_386   = 3
    EM_68K   = 4
    EM_88K   = 5
    EM_860   = 7
    EM_MIPS  = 8


class ElfVersion(Enum):
    EV_NONE    = 0
    EV_CURRENT = 1


class ElfSectionIndex(Enum):
    SHN_UNDEF     = 0
    SHN_LORESERVE = 0xff00
    SHN_LOPROC    = 0xff00
    SHN_HIPROC    = 0xff1f
    SHN_ABS       = 0xfff1
    SHN_COMMON    = 0xfff2
    SHN_HISERVE   = 0xffff


class ElfSectionType(Enum):
    SHT_NULL     = 0
    SHT_PROGBITS = 1
    SHT_SYMTAB   = 2
    SHT_STRTAB   = 3
    SHT_RELA     = 4
    SHT_HASH     = 5
    SHT_DYNAMIC  = 6
    SHT_NOTE     = 7
    SHT_NOBITS   = 8
    SHT_REL      = 9
    SHT_SHLIB    = 10
    SHT_DYNSYM   = 11
    SHT_LOPROC   = 0x70000000
    SHT_HIPROC   = 0x7fffffff
    SHT_LOUSER   = 0x80000000
    SHT_HIUSER   = 0xffffffff


class ElfHeader(Chunk):
    e_ident     = fields.ElfIdentField()
    e_type      = fields.StructField('H', default=ElfType.ET_EXEC.value)
    e_machine   = fields.StructField('H', default=ElfMachine.EM_386.value)
    e_version   = fields.StructField('I', default=ElfVersion.EV_CURRENT.value)
    e_entry     = fields.StructField('I')
    e_phoff     = fields.StructField('I')
    e_shoff     = fields.StructField('I')
    e_flags     = fields.StructField('I')
    e_ehsize    = fields.StructField('H', equals_to=Dependency('size'))
    e_phentsize = fields.StructField('H')
    e_phnum     = fields.StructField('H')
    e_shentsize = fields.StructField('H')
    e_shnum     = fields.StructField('H')
    e_shstrndx  = fields.StructField('H')

class SectionHeader(Chunk):
    sh_name      = fields.StructField('i')
    sh_type      = fields.StructField('i')
    sh_flags     = fields.StructField('i')
    sh_addr      = fields.StructField('i')
    sh_offset    = fields.StructField('i')
    sh_size      = fields.StructField('i')
    sh_link      = fields.StructField('i')
    sh_info      = fields.StructField('i')
    sh_addralign = fields.StructField('i')
    sh_entsize   = fields.StructField('i')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.data = None

    def unpack(self, stream):
        super().unpack(stream)

        # since can be present other fields at this
        # offset that we need to unpack, we save
        # the offset
        stream.save()

        # seek to the data we need
        stream.seek(self.sh_offset.value)
        # read it
        self.data = stream.read(self.sh_size.value)

        # and and restore the saved offset
        stream.restore()

class ElfFile(Chunk):
        elf_header = fields.ElfHeaderField()
        sections   = fields.ArrayField(SectionHeader, n=Dependency('elf_header.e_shnum'), offset=Offset('elf_header.e_shoff'))

