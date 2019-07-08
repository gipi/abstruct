'''
http://www.sco.com/developers/devspecs/gabi41.pdf
'''
from enum import Enum

from ...core import Chunk, Dependency
from .fields import * # TODO: use elf_fields
from .enum import *
from ... import fields
from ...properties import Offset


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

# TODO: is this the representation of the section headers or also of the
#       section associated? in the latter we need to calculate the offset
#       of the sections taking into account that also the headers of the
#       segments must precede them!
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


class ProgramHeader(Chunk):
    p_type   = fields.StructField('I')
    p_offset = fields.StructField('I')
    p_vaddr  = fields.StructField('I')
    p_paddr  = fields.StructField('I')
    p_filesz = fields.StructField('I')
    p_memsz  = fields.StructField('I')
    p_flags  = fields.StructField('I')
    p_align  = fields.StructField('I')


class ElfFile(Chunk):
    elf_header = fields.ElfHeaderField()
    sections   = fields.ArrayField(SectionHeader, n=Dependency('elf_header.e_shnum'), offset=Dependency('elf_header.e_shoff'))
    programs   = fields.ArrayField(ProgramHeader, n=Dependency('elf_header.e_phnum'), offset=Dependency('elf_header.e_phoff'))
    sections_data = ELFSectionsField(Dependency('sections'))
    segments_data = ELFSegmentsField(Dependency('programs'))

