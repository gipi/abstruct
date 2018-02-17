from .core import *


class ElfHeader(Chunk):
    fields = (
        ('e_ident',     StringField(16, default='\x7fELF\x01\x01\x01')), # FIXME
        ('e_type',      StructField('H', default=0x2)), # ET_EXEC
        ('e_machine',   StructField('H', default=0x3)), # EM_386
        ('e_version',   StructField('I', default=0x1)), # Version 1
        ('e_entry',     'I'),
        ('e_phoff',     'I'),
        ('e_shoff',     'I'),
        ('e_flags',     'I'),
        ('e_ehsize',    'H'),
        ('e_phentsize', 'H'),
        ('e_phnum',     'H'),
        ('e_shentsize', 'H'),
        ('e_shnum',     'H'),
        ('e_shstrndx',  'H'),
    )

class SectionHeader(Chunk):
    fields = (
        ('sh_name',      'i'),
        ('sh_type',      'i'),
        ('sh_flags',     'i'),
        ('sh_addr',      'i'),
        ('sh_offset',    'i'),
        ('sh_size',      'i'),
        ('sh_link',      'i'),
        ('sh_info',      'i'),
        ('sh_addralign', 'i'),
        ('sh_entsize',   'i'),
    )

class ElfFile(Chunk):
    fields = (
        ('elf_header', ElfHeader()),
    )

