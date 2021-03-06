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
from typing import List, Tuple

from ...core import Chunk, Field
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
    ElfSectionFlag,
)
from ... import fields


class ElfHeader(Chunk):
    """Header of an ELF file, the same for 32/64bit"""
    e_ident     = elf_fields.ElfIdent()
    e_type      = elf_fields.Elf_Half(enum=ElfType, default=ElfType.ET_EXEC)
    e_machine   = elf_fields.Elf_Half(enum=ElfMachine, default=ElfMachine.EM_386)
    e_version   = elf_fields.Elf_Word(enum=ElfVersion, default=ElfVersion.EV_CURRENT)
    e_entry     = elf_fields.Elf_Addr()
    e_phoff     = elf_fields.Elf_Off()
    e_shoff     = elf_fields.Elf_Off()
    e_flags     = elf_fields.Elf_Word()  # FIXME: this is processor specifics
    e_ehsize    = elf_fields.Elf_Half(equals_to=Dependency('.size'))
    e_phentsize = elf_fields.Elf_Half(default=32)  # FIXME: needs to be related to the actual size
    e_phnum     = elf_fields.Elf_Half()
    e_shentsize = elf_fields.Elf_Half(default=40)  # FIXME: needs to be related to the actual size
    e_shnum     = elf_fields.Elf_Half()
    e_shstrndx  = elf_fields.Elf_Half()


# TODO: is this the representation of the section headers or also of the
#       section associated? in the latter we need to calculate the offset
#       of the sections taking into account that also the headers of the
#       segments must precede them!
class SectionHeader(Chunk):
    sh_name      = elf_fields.Elf_Word()
    sh_type      = elf_fields.Elf_Word(enum=ElfSectionType, default=ElfSectionType.SHT_NULL)
    sh_flags     = elf_fields.Elf_Xword(enum=ElfSectionFlag)
    sh_addr      = elf_fields.Elf_Addr()
    sh_offset    = elf_fields.Elf_Off()
    sh_size      = elf_fields.Elf_Xword()
    sh_link      = elf_fields.Elf_Word()
    sh_info      = elf_fields.Elf_Word()
    sh_addralign = elf_fields.Elf_Xword()
    sh_entsize   = elf_fields.Elf_Xword()

    def get_name(self) -> str:
        """Get the section name directly from the associated string table (if exists)."""
        # the first parent is the ArrayField
        elf: ElfFile = self.father.father

        if not isinstance(elf, ElfFile):
            raise AttributeError(f'I could not find an associated string table to obtain the name')

        return elf.get_name_for_header(self)


class SegmentHeader(Chunk):
    '''This entity represent runtime information of the executable.

    Note: the field "p_flags"'s position depends on the ELF class.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._elf_class = Dependency('header.e_ident.EI_CLASS')

    def get_fields(self) -> List[Tuple[str, Field]]:
        original_fields = super().get_fields()
        if self._elf_class == ElfEIClass.ELFCLASS32:
            return original_fields

        order_for_64 = [
            'p_type',
            'p_flags',
            'p_offset',
            'p_vaddr',
            'p_paddr',
            'p_filesz',
            'p_memsz',
            'p_align',
        ]

        dict_orig_fields = dict(original_fields)

        return [(_label, dict_orig_fields[_label]) for _label in order_for_64]

    p_type   = elf_fields.Elf_Word(enum=ElfSegmentType, default=ElfSegmentType.PT_NULL)
    p_offset = elf_fields.Elf_Off()
    p_vaddr  = elf_fields.Elf_Addr()
    p_paddr  = elf_fields.Elf_Addr()
    p_filesz = elf_fields.Elf_Xword()
    p_memsz  = elf_fields.Elf_Xword()
    p_flags  = elf_fields.Elf_Word(enum=ElfSegmentFlag)
    p_align  = elf_fields.Elf_Xword()


# A tricky part about the ELF format is that both sections and segments
# reference the same part of the file by offset and size indipendently.
class ElfFile(Chunk):
    header          = ElfHeader()
    sections_header = fields.ArrayField(SectionHeader(), n=Dependency('header.e_shnum'), offset=Dependency('header.e_shoff'))
    segments_header = fields.ArrayField(SegmentHeader(), n=Dependency('header.e_phnum'), offset=Dependency('header.e_phoff'))
    sections        = elf_fields.ELFSectionsField(Dependency('sections_header'))
    segments        = elf_fields.ELFSegmentsField(Dependency('segments_header'))

    @property
    def section_names_table(self):
        '''return the string SectionStringTable with the names of the sections'''
        return self.sections.value[self.header.e_shstrndx.value]

    @property
    def symbol_names_table(self):
        return self.get_section_by_name('.strtab')

    @property
    def dynamic_symbol_names_table(self):
        return self.get_section_by_name('.dynstr')  # FIXME: find this using the dynamic segment

    def get_name_for_header(self, header: SectionHeader) -> str:
        return self.section_names_table.get(header.sh_name.value)

    @property
    def section_names(self) -> List[str]:
        sections_names = [self.get_name_for_header(_) for _ in self.sections_header.value]

        return sections_names

    def get_section_by_name(self, name):
        sections_names = self.section_names
        index = sections_names.index(name)

        return self.sections.value[index]

    def get_section_header_by_address(self, address: int) -> SectionHeader:
        for section in self.sections_header:
            if section.sh_addr.value <= address < (section.sh_addr.value + section.sh_size.value):
                return section

        return None

    def get_section_by_address(self, address: int) -> Tuple[SectionHeader, Field]:
        result_section_h = None
        result_section = None

        for idx, section in enumerate(self.sections_header):
            if section.sh_addr.value <= address < (section.sh_addr.value + section.sh_size.value):
                result_section_h = section
                break
        else:
            raise ValueError(f'no section with such address {address:x}')

        result_section = self.sections.value[idx]

        return result_section_h, result_section

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
        an instance of ElfDynamicSegmentField.'''
        dyn = None
        for segment in self.segments.value:
            if isinstance(segment, elf_fields.ElfDynamicSegmentField):
                dyn = segment
                break

        return dyn
