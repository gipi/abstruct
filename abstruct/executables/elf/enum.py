'''
This module contains the constant values used throught the ELF specification.

Note: use Enum for value that cannot ORed together, Flag for the others.
'''
from enum import Enum, Flag


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
    EM_S370  = 9
    EM_MIPS_RS3_LE = 10
    EM_PARISC = 15
    EM_VPP500 = 17
    EM_SPARC32PLUS = 18
    EM_960    = 19
    EM_PPC    = 20
    EM_PPC64  = 21
    EM_S390   = 22
    EM_SPU    = 23
    EM_V800   = 36
    EM_FR20   = 37
    EM_RH32   = 38
    EM_RCE    = 39
    EM_ARM    = 40
    EM_ALPHA  = 41
    EM_SH     = 42
    EM_SPARCV9 = 43
    EM_TRICORE = 44
    EM_ARC     = 45
    EM_H8_300  = 46
    EM_H8_300H = 47
    EM_H8S     = 48
    EM_H8_500  = 49
    EM_IA_64   = 50
    #EM_MIPS_X
    #EM_COLDFIRE
    #EM_68HC12
    EM_MMA = 54
    EM_PCP = 55
    EM_NCPU = 56
    EM_NDR1 = 57
    EM_STARCORE = 58
    EM_ME16 = 59
    EM_ST100 = 60
    EM_TINYJ = 61
    EM_X86_64 = 62
    EM_PDSP = 63
    EM_PDP10 = 64
    EM_PDP11 = 65
    EM_FX66 = 66
    EM_ST9PLUS = 67
    EM_ST7 = 68
    EM_68HC16 = 69
    EM_68HC11 = 70
    EM_68HC08 = 71
    EM_68HC05 = 72
    EM_SVX = 73
    EM_ST19 = 74
    EM_VAX = 75
    EM_CRIS = 76
    EM_JAVELIN = 77
    EM_FIREPATH = 78
    EM_ZSP = 79
    EM_MMIX = 80
    EM_HUANY = 81
    EM_PRISM = 82
    EM_AVR = 83
    EM_FR30 = 84
    EM_D10V = 85
    EM_D30V = 86
    EM_V850 = 87
    EM_M32R = 88
    EM_MN10300 = 89
    EM_MN10200 = 90
    EM_PJ = 91
    EM_OPENRISC = 92
    EM_ARC_COMPACT = 93
    EM_XTENSA = 94
    EM_VIDEOCORE = 95
    EM_TMM_GPP = 96
    EM_NS32K = 97
    EM_TPC = 98
    EM_SNP1K = 99
    EM_ST200 = 100
    EM_IP2K = 101
    EM_MAX = 102
    EM_CR = 103
    EM_F2MC16 = 104
    EM_MSP430 = 105
    EM_BLACKFIN = 106
    EM_SE_C33 = 107
    EM_SEP = 108
    EM_ARCA = 109
    EM_UNICORE = 110
    EM_EXCESS = 111
    EM_DXP = 112
    EM_ALTERA_NIOS2 = 113
    EM_CRX = 114
    #EM_XGATE
    EM_C166 = 116
    EM_M16C = 117
    #EM_DSPIC30F
    EM_CE = 119
    EM_M32C = 120
    EM_TSK3000 = 131
    EM_RS08 = 132
    '''
    EM_SHARC
    EM_ECOG2
    EM_SCORE7
    EM_DSP24
    EM_VIDEOCORE3
    EM_SE_C17
    EM_TI_C6000
    EM_TI_C2000
    EM_TI_C5500
    EM_TI_ARP32
    EM_TI_PRU
    EM_MMDSP_PLUS
    EM_MMDSP_PLUS
    EM_CYPRESS_M8C
    EM_R32C = 162
    #EM_TRIMEDIA
    #EM_QDSP6
    EM_8051 = 165
    EM_STXP7X
    EM_NDS32
    EM_ECOG1
    EM_ECOG1X
    EM_MAXQ30
    EM_XIMO16
    #EM_MANIK
    #EM_CRAYNV2
    EM_RX = 173
    #EM_METAG
    #EM_MCST_ELBRUS
    #EM_ECOG16
    EM_CR16 = 177
    EM_ETPU = 178
    #EM_SLE9X
    EM_L10M = 180
    EM_K10M = 181
    #EM_AARCH64
    #EM_AVR32
    EM_STM8 = 186
    #EM_TILE64
    #EM_TILEPRO
    #EM_MICROBLAZE
    EM_CUDA = 190
    #EM_TILEGX
    #EM_CLOUDSHIELD
    #EM_COREA_1ST
    #EM_COREA_2ND
    #EM_ARC_COMPACT2
    #EM_OPEN8
    EM_RL78 = 197
    #EM_VIDEOCORE5
    #EM_78KOR
    #EM_56800EX
    EM_BA1 = 201
    EM_BA2 = 202
    #EM_XCORE
    #EM_MCHP_PIC
    #EM_INTEL205
    #EM_INTEL206
    #EM_INTEL207
    #EM_INTEL208
    #EM_INTEL209
    EM_KM32 = 210
    #EM_KMX32
    #EM_KMX16
    EM_KMX8 = 213
    #EM_KVARC
    EM_CDP = 215
    EM_COGE = 216
    EM_COOL = 217
    EM_NORC = 218
    #EM_CSR_KALIMBA
    EM_Z80 = 220
    #EM_VISIUM
    EM_FT32 = 222'''


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


class ElfOsABI(Enum):
    ELFOSABI_NONE = 0
    ELFOSABI_HPUX = 1
    ELFOSABI_NETBSD = 2
    ELFOSABI_GNU = 3
    ELFOSABI_SOLARIS = 6
    ELFOSABI_AIX = 7
    ELFOSABI_IRIX = 8
    ELFOSABI_FREEBSD = 9
    ELFOSABI_TRU64 = 10
    ELFOSABI_MODESTO = 11
    ELFOSABI_OPENBSD = 12
    ELFOSABI_OPENVMS = 13
    ELFOSABI_NSK = 14
    ELFOSABI_AROS = 15
    ELFOSABI_FENIXOS = 16
    ELFOSABI_CLOUDABI = 17
    ELFOSABI_OPENVOS = 18


class ElfSegmentType(Enum):
    PT_NULL = 0
    PT_LOAD = 1
    PT_DYNAMIC = 2
    PT_INTERP  = 3
    PT_NOTE    = 4
    PT_SHLIB   = 5
    PT_PHDR    = 6
    PT_TLS     = 7
    # see <https://docs.oracle.com/cd/E19120-01/open.solaris/819-0690/chapter6-14428/index.html>
    PT_LOOS  = 0x60000000
    PT_SUNW_UNWIND = 0x6464e550
    # see <https://refspecs.linuxfoundation.org/LSB_4.0.0/LSB-Core-generic/LSB-Core-generic.html#PROGHEADER>
    PT_SUNW_EH_FRAME = 0x6474e550
    PT_GNU_EH_FRAME = 0x6474e550
    PT_GNU_STACK = 0x6474e551
    PT_GNU_RELRO = 0x6474e552
    PT_LOSUNW = 0x6ffffffa
    PT_SUNWBSS = 0x6ffffffa
    PT_SUNWSTACK = 0x6ffffffb
    PT_SUNWDTRACE = 0x6ffffffc
    PT_SUNWCAP = 0x6ffffffd
    PT_HISUNW = 0x6fffffff
    PT_HIOS = 0x6fffffff
    PT_LOPROC  = 0x70000000
    PT_HIPROC  = 0x7fffffff


class ElfSegmentFlag(Flag):
    PF_X = 0x01
    PF_W = 0x02
    PF_R = 0x04


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


class ElfSymbolBindType(Enum):
    STB_LOCAL  = 0x00
    STB_GLOBAL = 0x01
    STB_WEAK   = 0x02
    STB_NUM    = 0x03
    STB_LOPROC = 13
    STB_HIPROC = 15


class ElfSymbolType(Enum):
    STT_NOTYPE = 0x00
    STT_OBJECT = 0x01
    STT_FUNC   = 0x02
    STT_SECTION = 0x03
    STT_FILE   = 0x04
    STT_LOPROC = 13
    STT_HIPROC = 15


class ElfDynamicTagType(Enum):
    DT_NULL     = 0x00
    DT_NEEDED   = 0x01
    DT_PLTRELSZ = 0x02
    DT_PLTGOT   = 0x03
    DT_HASH     = 0x04
    DT_STRTAB   = 0x05
    DT_SYMTAB   = 0x06
    DT_RELA     = 0x07
    DT_RELASZ   = 0x08
    DT_RELAENT  = 0x09
    DT_STRSZ    = 0x0a
    DT_SYMENT   = 0x0b
    DT_INIT     = 0x0c
    DT_FINI     = 0x0d
    DT_SONAME   = 0x0e
    DT_RPATH    = 0x0f
    DT_SYMBOLIC = 0x10
    DT_REL      = 0x11
    DT_RELSZ    = 0x12
    DT_RELENT   = 0x13
    DT_PLTREL   = 0x14
    DT_DEBUG    = 0x15
    DT_TEXTREL  = 0x16
    DT_JMPREL   = 0x17
    DT_BIND_NOW = 0x18
    DT_INIT_ARRAY = 0x19
    DT_FINI_ARRAY = 0x1a
    DT_INIT_ARRAYSZ = 0x1b
    DT_FINI_ARRAYSZ = 0x1c
    DT_RUNPATH  = 0x1d
    DT_FLAGS    = 0x1e
    DT_ENCODING = 0x1f
    DT_PREINIT_ARRAY = 0x20
    DT_PREINIT_ARRAYSZ = 0x21
    DT_SYMTAB_SHNDX = 0x22
    DT_GNU_HASH    = 0x6ffffef5
    DT_VERSYM      = 0x6ffffff0
    DT_RELACOUNT   = 0x6ffffff9
    DT_RELCOUNT    = 0x6ffffffa
    DT_FLAGS_1     = 0x6ffffffb
    DT_VERDEF      = 0x6ffffffc
    DT_VERDEFNUM   = 0x6ffffffd
    DT_VERNEED     = 0x6ffffffe
    DT_VERNEEDNUM  = 0x6fffffff
    OLD_DT_HIOS = 0x6fffffff
    DT_LOPROC   = 0x70000000
    DT_HIPROC   = 0x7fffffff


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
