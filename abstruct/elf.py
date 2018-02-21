from .core import *
from .fields import *
from .properties import Offset



class ElfHeader(Chunk):
    e_ident     = StringField(16, default=b'\x7fELF\x01\x01\x01') # FIXME
    e_type      = StructField('H', default=0x2) # ET_EXEC
    e_machine   = StructField('H', default=0x3) # EM_386
    e_version   = StructField('I', default=0x1) # Version 1
    e_entry     = StructField('I') # Version 1'I'
    e_phoff     = StructField('I') # Version 1'I'
    e_shoff     = StructField('I') # Version 1'I'
    e_flags     = StructField('I') # Version 1'I'
    e_ehsize    = StructField('H') # Version 1'H'
    e_phentsize = StructField('H') # Version 1'H'
    e_phnum     = StructField('H') # Version 1'H'
    e_shentsize = StructField('H') # Version 1'H'
    e_shnum     = StructField('H') # Version 1'H'
    e_shstrndx  = StructField('H') # Version 1'H'

class SectionHeader(Chunk):
        sh_name=      StructField('i')
        sh_type=      StructField('i')
        sh_flags=     StructField('i')
        sh_addr=      StructField('i')
        sh_offset=    StructField('i')
        sh_size=      StructField('i')
        sh_link=      StructField('i')
        sh_info=      StructField('i')
        sh_addralign= StructField('i')
        sh_entsize=   StructField('i')

class ElfFile(Chunk):
        elf_header = ElfHeader()
        sections =  ArrayField(SectionHeader, n='elf_header.sh_num', offset=Offset('elf_header.e_shoff'))

