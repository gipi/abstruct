'''
# ELF format

There are two main aspects of that this format take into consideration

 1. how to statically link
 2. how to load a program in memory and to execute it

Reference to <http://www.sco.com/developers/devspecs/gabi41.pdf>.


This <http://www.sco.com/developers/gabi/latest/contents.html> seems
a more complete reference for the format (take into consideration that exist a general
reference (linked before) and then each architecture has its own document that address
specific aspect).
'''
from ...core import Chunk
from ...properties import Dependency
from . import fields as elf_fields
from .enum import (
    ElfEIClass,
    ElfType,
    ElfMachine,
    ElfVersion,
    ElfSectionType,
    ElfSegmentType,
    ElfSegmentFlag,
)
from ... import fields


class ElfHeader(Chunk):
    e_ident     = fields.ElfIdentField()
    e_type      = elf_fields.Elf_Half(enum=ElfType, default=ElfType.ET_EXEC)
    e_machine   = elf_fields.Elf_Half(enum=ElfMachine, default=ElfMachine.EM_386)
    e_version   = elf_fields.Elf_Word(enum=ElfVersion, default=ElfVersion.EV_CURRENT)
    e_entry     = elf_fields.Elf_Addr()
    e_phoff     = elf_fields.Elf_Off()
    e_shoff     = elf_fields.Elf_Off()
    e_flags     = elf_fields.Elf_Word()
    e_ehsize    = elf_fields.Elf_Half(equals_to=Dependency('size'))
    e_phentsize = elf_fields.Elf_Half()
    e_phnum     = elf_fields.Elf_Half()
    e_shentsize = elf_fields.Elf_Half()
    e_shnum     = elf_fields.Elf_Half()
    e_shstrndx  = elf_fields.Elf_Half()


# TODO: is this the representation of the section headers or also of the
#       section associated? in the latter we need to calculate the offset
#       of the sections taking into account that also the headers of the
#       segments must precede them!
class SectionHeader(Chunk):
    sh_name      = elf_fields.Elf_Word()
    sh_type      = elf_fields.Elf_Word(enum=ElfSectionType, default=ElfSectionType.SHT_NULL)
    sh_flags     = elf_fields.Elf_Xword()
    sh_addr      = elf_fields.Elf_Addr()
    sh_offset    = elf_fields.Elf_Off()
    sh_size      = elf_fields.Elf_Xword()
    sh_link      = elf_fields.Elf_Word()
    sh_info      = elf_fields.Elf_Word()
    sh_addralign = elf_fields.Elf_Xword()
    sh_entsize   = elf_fields.Elf_Xword()


class ProgramHeader(Chunk):
    '''This entity represent runtime information of the executable.

    Note: the field "p_flags"'s position depends on the ELF class.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._elf_class = Dependency('elf_header.e_ident.EI_CLASS')

    def get_fields(self):
        original_fields = super().get_fields()
        # FIXME: here we need to call resolve() by ourself since it's not a field
        if self._elf_class.resolve(self) == ElfEIClass.ELFCLASS32:
            return original_fields

        ORDERING_64 = [
            'p_type',
            'p_flags',
            'p_offset',
            'p_vaddr',
            'p_paddr',
            'p_filesz',
            'p_memsz',
            'p_align',
        ]
        modified_fields = []
        # FIXME: this is shit
        for name in ORDERING_64:
            for _ in original_fields:
                if _[0] == name:
                    modified_fields.append(_)
                    break

        return modified_fields

    p_type   = elf_fields.Elf_Word(enum=ElfSegmentType, default=ElfSegmentType.PT_NULL)
    p_offset = elf_fields.Elf_Off()
    p_vaddr  = elf_fields.Elf_Addr()
    p_paddr  = elf_fields.Elf_Addr()
    p_filesz = elf_fields.Elf_Xword()
    p_memsz  = elf_fields.Elf_Xword()
    p_flags  = elf_fields.Elf_Word(enum=ElfSegmentFlag)
    p_align  = elf_fields.Elf_Xword()


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
    def dynamic_symbol_names_table(self):
        return self.get_section_by_name('.dynstr')

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
    def dynamic_symbol_names(self):
        return self.dynamic_symbol_names_table.value

    @property
    def symbols(self):
        symbols_table = self.get_section_by_name('.symtab')

        symbols_table_names = self.symbol_names_table

        return {symbols_table_names.get(_.st_name.value): _ for _ in symbols_table.value}

    @property
    def dyn_symbols(self):
        dyn_symbols_table = self.get_section_by_name('.dynsym')

        dyn_symbols_table_names = self.dynamic_symbol_names_table

        return {dyn_symbols_table_names.get(_.st_name.value): _ for _ in dyn_symbols_table.value}

    @property
    def dynamic(self):
        '''It returns the dynamic segment of the ELF executable if it exists, i.e.
        an instance of RealElfDynamicSegmentField.'''
        dyn = None
        for segment in self.segments_data.value:
            if isinstance(segment, elf_fields.RealElfDynamicSegmentField):
                dyn = segment
                break

        return dyn
