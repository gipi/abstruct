from enum import Enum


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


class ElfEIClass(Enum):
    ELFCLASSNONE = 0
    ELFCLASS32   = 1
    ELFCLASS64   = 2


class ElfEIData(Enum):
    ELFDATANONE = 0
    ELFDATA2LSB = 1
    ELFDATA2MSB = 2


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
    # see <https://docs.oracle.com/cd/E19120-01/open.solaris/819-0690/6n33n7fcj/index.html>
    SHT_INIT_ARRAY = 14
    SHT_FINI_ARRAY = 15
    SHT_PREINIT_ARRAY = 16
    SHT_GROUP = 17
    SHT_SYMTAB_SHNDX = 18
    SHT_SUNW_SIGNATURE = 0x6ffffff6
    SHT_SUNW_verneed = 0x6ffffffe
    SHT_SUNW_versym = 0x6fffffff
    SHT_LOPROC   = 0x70000000
    SHT_HIPROC   = 0x7fffffff
    SHT_LOUSER   = 0x80000000
    SHT_HIUSER   = 0xffffffff

class ElfSectionAttributeFlag(Enum):
    SHF_WRITE     = 0x01
    SHF_ALLOC     = 0x02
    SHF_EXECINSTR = 0x04

