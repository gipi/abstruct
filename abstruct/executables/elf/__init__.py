'''
# ELF format

There are two main aspects of that this format take into consideration

 1. how to statically link
 2. how to load a program in memory and to execute it

Reference to <http://www.sco.com/developers/devspecs/gabi41.pdf>.

This <https://docs.oracle.com/cd/E19120-01/open.solaris/819-0690/6n33n7fcd/index.html> seems
a more complete reference for the format (take into consideration that exist a general
reference (linked before) and then each architecture has its own document that address
specific aspect).
'''
from ...core import Chunk, Dependency
from . import fields as elf_fields
from .enum import (
    ElfType,
    ElfMachine,
    ElfVersion,
    ElfSectionType,
    ElfSegmentType,
    ElfSegmentFlag,
)
from ... import fields
from ...properties import Offset


class ElfHeader(Chunk):
    e_ident     = fields.ElfIdentField()
    e_type      = fields.BitField(ElfType, 'H', default=ElfType.ET_EXEC)
    e_machine   = fields.BitField(ElfMachine, 'H', default=ElfMachine.EM_386)
    e_version   = fields.BitField(ElfVersion, 'I', default=ElfVersion.EV_CURRENT)
    e_entry     = elf_fields.Elf_Addr()
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
    sh_type      = fields.BitField(ElfSectionType, 'i', default=ElfSectionType.SHT_NULL)
    sh_flags     = fields.StructField('i')
    sh_addr      = fields.StructField('i')
    sh_offset    = fields.StructField('i')
    sh_size      = fields.StructField('i')
    sh_link      = fields.StructField('i')
    sh_info      = fields.StructField('i')
    sh_addralign = fields.StructField('i')
    sh_entsize   = fields.StructField('i')


class ProgramHeader(Chunk):
    p_type   = fields.BitField(ElfSegmentType, 'I', default=ElfSegmentType.PT_NULL)
    p_offset = fields.StructField('I')
    p_vaddr  = fields.StructField('I')
    p_paddr  = fields.StructField('I')
    p_filesz = fields.StructField('I')
    p_memsz  = fields.StructField('I')
    p_flags  = fields.BitField(ElfSegmentFlag, 'I')
    p_align  = fields.StructField('I')


class ElfFile(Chunk):
    elf_header = fields.ElfHeaderField()
    sections   = fields.ArrayField(SectionHeader, n=Dependency('elf_header.e_shnum'), offset=Dependency('elf_header.e_shoff'))
    programs   = fields.ArrayField(ProgramHeader, n=Dependency('elf_header.e_phnum'), offset=Dependency('elf_header.e_phoff'))
    sections_data = elf_fields.ELFSectionsField(Dependency('sections'))
    segments_data = elf_fields.ELFSegmentsField(Dependency('programs'))

    @property
    def section_names_table(self):
        '''return the string SectionStringTable with the names of the sections'''
        return self.sections_data.value[self.elf_header.e_shstrndx.value]

    @property
    def symbol_names_table(self):
        return self.get_section_by_name('.strtab')

    @property
    def section_names(self):
        string_table = self.section_names_table
        sections_names = [string_table.get(_.sh_name.value) for _ in self.sections.value]

        return sections_names

    def get_section_by_name(self, name):
        sections_names = self.section_names
        index = sections_names.index(name)

        return self.sections_data.value[index]

    @property
    def symbol_names(self):
        return self.symbol_names_table.value

    @property
    def symbols(self):
        symbols_table = self.get_section_by_name('.symtab')

        symbols_table_names = self.symbol_names_table

        return {symbols_table_names.get(_.st_name.value): _ for _ in symbols_table.value}

