'''
# Elf format

Executable and Linkage Format is a file format vastly used in the *nix world.

'''
import logging
from typing import List

from ... import fields
from ...core import Chunk
from .enum import (
    Enum,
    ElfMachine,
    ElfEIClass,
    ElfEIData,
    ElfOsABI,
    ElfSectionType,
    ElfSegmentType,
    ElfSymbolBindType,
    ElfSymbolType,
    ElfDynamicTagType,
)
from ...properties import Dependency
from ...streams import Stream
from ...exceptions import UnrecoverableException


class ElfIdent(Chunk):
    EI_MAG0 = fields.StructField('c', default=b'\x7f', is_magic=True)
    EI_MAG1 = fields.StructField('c', default=b'E', is_magic=True)
    EI_MAG2    = fields.StructField('c', default=b'L', is_magic=True)
    EI_MAG3    = fields.StructField('c', default=b'F', is_magic=True)
    EI_CLASS   = fields.StructField('B', enum=ElfEIClass, default=ElfEIClass.ELFCLASS32)  # determines the architecture
    EI_DATA    = fields.StructField('B', enum=ElfEIData, default=ElfEIData.ELFDATA2LSB)  # determines the endianess of the binary data
    EI_VERSION = fields.StructField('B', default=1)  # always 1
    EI_OSABI   = fields.StructField('B', enum=ElfOsABI, default=ElfOsABI.ELFOSABI_GNU)
    EI_ABIVERSION = fields.StructField('B')
    EI_PAD     = fields.StringField(7)

    def check_magic(self):
        return self.EI_MAG0.value == b'\x7f' or self.EI_MAG1.value == b'E' or self.EI_MAG2.value == b'L' or self.EI_MAG3.value == b'F'


# TODO: create BoolFromDependency that use the EI_CLASS from the ELF header
#       and generates the endianess to pass via the little_endian parameter.
class Elf_DataType(fields.StructField):
    '''Wrapper for all the datatype that resolves internally to the EI_CLASS'''

    def __init__(self, **kwargs):
        kwargs['endianess'] = Dependency('header.e_ident.EI_DATA')
        super().__init__('I', **kwargs)
        self._elf_class = Dependency('header.e_ident.EI_CLASS')

    def get_format(self):
        if not isinstance(self._elf_class, Enum):
            self.logger.error(f'EI_CLASS has not a value useful')
            raise UnrecoverableException(chain=[])

        fmt = '%s%s' % (
            '<' if self.endianess == ElfEIData.ELFDATA2LSB else '>',
            self.MAP_CLASS_TYPE[self._elf_class],
        )
        self.logger.debug(f'format: \'{fmt}\'')

        return fmt


class Elf_Addr(Elf_DataType):
    '''Unsigned program address'''

    MAP_CLASS_TYPE = {
        ElfEIClass.ELFCLASS32: 'I',
        ElfEIClass.ELFCLASS64: 'Q',
    }


class Elf_Off(Elf_DataType):
    '''Unsigned file offset'''

    MAP_CLASS_TYPE = {
        ElfEIClass.ELFCLASS32: 'I',
        ElfEIClass.ELFCLASS64: 'Q',
    }


class Elf_Sword(Elf_DataType):
    '''Wrapper for the fundamental datatype of the ELF format'''

    MAP_CLASS_TYPE = {
        ElfEIClass.ELFCLASS32: 'I',
        ElfEIClass.ELFCLASS64: 'I',
    }


class Elf_Xword(Elf_DataType):
    ''''''

    MAP_CLASS_TYPE = {
        ElfEIClass.ELFCLASS32: 'I',
        ElfEIClass.ELFCLASS64: 'Q',
    }


class Elf_Sxword(Elf_DataType):

    MAP_CLASS_TYPE = {
        ElfEIClass.ELFCLASS32: 'I',  # This mean Elf_Sword for 32
        ElfEIClass.ELFCLASS64: 'Q',
    }


class Elf_Word(Elf_DataType):
    '''Wrapper for the fundamental datatype of the ELF format'''

    MAP_CLASS_TYPE = {
        ElfEIClass.ELFCLASS32: 'I',
        ElfEIClass.ELFCLASS64: 'I',
    }


class Elf_Half(Elf_DataType):
    '''Wrapper for the fundamental datatype of the ELF format'''

    MAP_CLASS_TYPE = {
        ElfEIClass.ELFCLASS32: 'H',
        ElfEIClass.ELFCLASS64: 'H',
    }


class ELFInterpol(Chunk):  # TODO: use StringField

    def __init__(self, *args, size=None, **kwargs):
        super().__init__(*args, **kwargs)

        self._size = size

    def unpack(self, stream):
        self.value = stream.read(self._size)


# TODO: maybe better subclass of Chunk with ArrayField as unique element?
class SectionStringTable(fields.Field):
    '''
    There are three string tables identified by their section name

        1. ".shstrtab" for section names (this is actually indicated by the e_shstrndx header field)
        2. ".strtab" names associated with the symbol table entries
        3. ".dynstr" names associated with dynamic linking
    '''

    def __init__(self, size=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._size = size
        # IMPORTANT: size is used for unpacking, default for packing!!!

    def get(self, index):
        '''return the string pointed at index'''
        st = self._contents[index:]

        return st[:st.find(b'\x00')].decode()

    def unpack(self, stream):
        '''read all the bytes and then build as many NULL terminated strings
        as possible'''
        self._contents = stream.read(self._size)
        last_index = 0

        strings = []

        for index in range(self._size):
            if self._contents[index] == 0:
                strings.append(self._contents[last_index + 1:index].decode())
                last_index = index

        self.value = strings

    def pack(self, stream=None):
        value = b''
        for string in self.value:
            value += string.encode() + b'\x00'

        stream.write(value)


class SymbolInfoField(fields.StructField):

    def __init__(self, *args, **kwargs):
        super().__init__('B', *args, **kwargs)

    def __repr__(self):
        return '<%s(%s,%s)>' % (self.__class__.__name__, self.bind, self.type)

    def unpack(self, stream):
        '''it reads and then split the values in bind and type'''
        super().unpack(stream)
        self.bind = ElfSymbolBindType(self.value >> 4)
        self.type = ElfSymbolType(self.value & 0x0f)


class SymbolTableEntry(Chunk):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._elf_class = Dependency('header.e_ident.EI_CLASS')

    def get_ordered_fields_name(self) -> List[str]:
        original_fields = super().get_ordered_fields_name()
        if self._elf_class == ElfEIClass.ELFCLASS32:
            return original_fields

        return [
            'st_name',
            'st_info',
            'st_other',
            'st_shndx',
            'st_value',
            'st_size',
        ]

    st_name  = Elf_Word()
    st_value = Elf_Addr()
    st_size  = Elf_Xword()
    st_info  = SymbolInfoField()
    st_other = fields.StringField(0x01)
    st_shndx = Elf_Half()


class SymbolTable(fields.ArrayField):

    def __init__(self, *args, **kwargs):
        super().__init__(SymbolTableEntry(), *args, **kwargs)


class DynamicEntry(Chunk):
    d_tag = Elf_Sxword(enum=ElfDynamicTagType)
    d_un  = Elf_Xword()  # FIXME: create UnionField


class ElfDynamicSegmentField(fields.ArrayField):

    def __init__(self, *args, size=None, father=None, **kwargs):
        super().__init__(DynamicEntry(), *args, n=int(size / DynamicEntry(father=father).size()), father=father, **kwargs)
        self._dict = {}

    def _resolve_entry_DT_NEEDED(self, entry, elf):
        # here we have to resolve the string pointed by the string table for the dynamic
        string_table_addr = self[ElfDynamicTagType.DT_STRTAB].d_un.value
        string_table_size = self[ElfDynamicTagType.DT_STRSZ].d_un.value
        segment = elf.segments.get_segment_for_address(string_table_addr)

        raw = segment.raw
        offset = string_table_addr - segment.vaddr

        string_table = SectionStringTable(size=string_table_size)
        stream = Stream(raw)
        stream.seek(offset)
        string_table.unpack(stream)

        return string_table.get(entry.d_un.value)

    def _resolve_entry_DT_SYMTAB_(self, entry, elf):
        from .reloc import ElfRelocationTable
        symbol_table_addr = entry.d_un_value
        symbol_table_entry_size = self[ElfDynamicTagType.DT_SYMENT].d_un.value
        segment = elf.segments.get_segment_for_address(symbol_table_addr)

        raw = segment.raw
        offset = symbol_table_addr - segment.vaddr

        symbol_table = ElfRelocationTable(size=symbol_table_entry_size, father=self.father)
        stream = Stream(raw)
        stream.seek(offset)
        symbol_table.unpack(stream)

        return symbol_table

    def _resolve_entry_DT_REL(self, entry, elf):
        from .reloc import ElfRelTable
        rel_table_addr = entry.d_un.value
        rel_table_size = self[ElfDynamicTagType.DT_RELSZ].d_un.value
        segment = elf.segments.get_segment_for_address(rel_table_addr)

        raw = segment.raw
        offset = rel_table_addr - segment.vaddr

        rel_table = ElfRelTable(size=rel_table_size, father=self.father)
        stream = Stream(raw)
        stream.seek(offset)
        rel_table.unpack(stream)

        return rel_table

    def _resolve_entry_DT_RELA(self, entry, elf):
        from .reloc import ElfRelaTable
        rel_table_addr = entry.d_un.value
        rel_table_size = self[ElfDynamicTagType.DT_RELASZ].d_un.value
        segment = elf.segments.get_segment_for_address(rel_table_addr)

        raw = segment.raw
        offset = rel_table_addr - segment.vaddr

        rela_table = ElfRelaTable(size=rel_table_size, father=self.father)
        stream = Stream(raw)
        stream.seek(offset)
        rela_table.unpack(stream)

        return rela_table

    def _resolve_entry_DT_PLTREL(self, entry, elf):
        return ElfDynamicTagType(entry.d_un.value)

    def _resolve_entry_default(self, entry, elf):
        self.logger.debug('not implemented')
        return None

    def get_symbol(self, idx):
        '''It return the symbol entry at index idx'''
        # the DT_SYMTAB is not resolvable because we don't have an explicit size for it
        # so we take the segment that contains it and read the entry at the given offset
        sym_table_addr = self[ElfDynamicTagType.DT_SYMTAB].d_un.value
        sym_entry_size = self[ElfDynamicTagType.DT_SYMENT].d_un.value

        elf = Dependency('@ElfFile').resolve_field(self)
        segment = elf.segments.get_segment_for_address(sym_table_addr)

        raw = segment.raw
        offset = sym_table_addr - segment.vaddr

        entry = SymbolTableEntry(father=self.father)

        stream = Stream(raw)
        stream.seek(offset + (idx * sym_entry_size))

        entry.unpack(stream)

        return entry

    def get_symbol_name(self, idx):
        return self.get_string_table().get(self.get_symbol(idx).st_name.value)

    def get_string_table(self):
        str_table_addr = self[ElfDynamicTagType.DT_STRTAB].d_un.value
        str_table_size = self[ElfDynamicTagType.DT_STRSZ].d_un.value

        elf = Dependency('@ElfFile').resolve_field(self)
        segment = elf.segments.get_segment_for_address(str_table_addr)

        raw = segment.raw
        offset = str_table_addr - segment.vaddr

        entry = SectionStringTable(size=str_table_size, father=self.father)

        stream = Stream(raw)
        stream.seek(offset)

        entry.unpack(stream)

        return entry

    def append(self, element):
        super().append(element)

        # save also in a dictionary using as keys the ElfDynamicTagType
        key = element.d_tag.value
        if key not in self._dict:
            self._dict[key] = element
        else:  # if there is already a key
            value = self._dict[key]
            if isinstance(value, list):  # and is is a list
                value.append(element)  # append
            else:
                self._dict[key] = [value, element]  # or create a list

    def __getitem__(self, key):
        return self._dict[key]

    def __contains__(self, item):
        return item in self._dict

    def get(self, typeOf):
        '''It returns something to which this instance points to'''
        element = self[typeOf]

        elf = Dependency('@ElfFile').resolve_field(self)

        callback_name = f'_resolve_entry_{element.d_tag.value.name}'

        try:
            callback = getattr(self, callback_name)
        except AttributeError:
            self.logger.warning(f'Unable to find a resolver for type {typeOf}')
            callback = self._resolve_entry_default

        field = callback(element, elf)

        return field


class ELFSectionsField(fields.Field):
    '''Handles the data pointed by an entry of the Section header
    TODO: how do entry from this and the corresponding header behave wrt each other?
          if we remove the header, we remove the entry and vice versa?
    '''

    def __init__(self, header, *args, **kwargs):
        '''Use the header parameter to get the entries needed'''
        super().__init__(*args, **kwargs)
        self.header = header  # this MUST be a Dependency

    def init(self):
        pass

    def size(self):
        size = 0
        for field in self.header:
            size += field.size()

        return size

    def pack(self, stream=None, relayout=True):
        '''TODO: we have to update also the corresponding header entries'''
        for field in self.header:
            self.logger.debug('pack()()()')

    def unpack(self, stream):
        self.value = []  # reset the entries
        for field in self.header:
            section_type = field.sh_type.value
            self.logger.debug('found section type %s' % section_type)
            self.logger.debug('offset: %d size: %d' % (field.sh_offset.value, field.sh_size.value))

            if section_type == ElfSectionType.SHT_STRTAB:
                self.logger.debug('unpacking string table')
                # we need to unpack at most sh_size bytes
                stream.seek(field.sh_offset.value)
                section = SectionStringTable(size=field.sh_size.value)
                section.unpack(stream)
                self.value.append(section)
            elif section_type == ElfSectionType.SHT_SYMTAB:
                table_size = field.sh_size.value
                self.logger.debug('unpacking symbol table')
                n = int(table_size / SymbolTableEntry(father=self).size())  # FIXME: create Dependency w algebraic operation
                self.logger.debug(' with %d entries' % n)

                stream.seek(field.sh_offset.value)

                section = SymbolTable(n=n, father=self)
                section.unpack(stream)

                self.value.append(section)
            elif section_type == ElfSectionType.SHT_DYNSYM:
                table_size = field.sh_size.value
                self.logger.debug('unpacking dynamic symbol table')
                n = int(table_size / SymbolTableEntry(father=self).size())  # FIXME: create Dependency w algebraic operation
                self.logger.debug(' with %d entries' % n)

                stream.seek(field.sh_offset.value)

                section = SymbolTable(n=n, father=self)
                section.unpack(stream)

                self.value.append(section)
            elif section_type == ElfSectionType.SHT_REL:
                from .reloc import ElfRelTable
                from .reloc import ElfRelEntry
                table_size = field.sh_size.value

                self.logger.debug('unpacking relocation table')
                n = int(table_size / ElfRelEntry(father=self).size())  # FIXME: create Dependency w algebraic operation
                self.logger.debug(' with %d entries' % n)

                stream.seek(field.sh_offset.value)

                section = ElfRelTable(n=n, father=self)
                section.unpack(stream)

                self.value.append(section)
            else:
                self.logger.debug('unpacking unhandled data of type %s' % section_type)
                stream.seek(field.sh_offset.value)
                section = fields.StringField(field.sh_size.value)
                section.unpack(stream)

                self.value.append(section)


class ELFSegmentsField(fields.Field):
    '''Handles the data pointed by an entry of the program header
    TODO: how do entry from this and the corresponding header behave wrt each other?
          if we remove the header, we remove the entry and vice versa?
    '''

    def __init__(self, header, *args, **kwargs):
        '''Use the header parameter to get the entries needed'''
        super().__init__(*args, **kwargs)
        self.header = header  # this MUST be a Dependency
        self.default = [] if 'default' not in kwargs else kwargs['default']

    def init(self):
        pass

    def size(self):
        size = 0
        for field in self.header:
            size += field.size()

        return size

    def __len__(self):
        return len(self.value)

    def get_segment_for_address(self, addr):
        '''It returns the entry that contains the address specified'''
        segments_header = Dependency('segments_header').resolve(self)

        for idx, segment in enumerate(segments_header):
            if segment.p_vaddr.value <= addr < (segment.p_vaddr.value + segment.p_memsz.value):
                return self.value[idx]

        return None

    def pack(self, stream=None, relayout=True):
        '''TODO: we have to update also the corresponding header entries'''
        raw = b''
        for field in self.value:
            self.logger.debug('pack()()()')
            raw += field.pack(stream)  # FIXME: if stream is None

        return raw

    def _handle_unpack_PT_PHDR(self, entry):
        '''It handles the header, simply using a StringField'''
        field = fields.StringField(n=entry.p_filesz.value)

        return field

    def _handle_unpack_PT_INTERP(self, entry):
        interp = ELFInterpol(offset=entry.p_offset.value, size=entry.p_filesz.value)

        return interp

    def _handle_unpack_PT_DYNAMIC(self, entry):
        dyn = ElfDynamicSegmentField(offset=entry.p_offset.value, size=entry.p_filesz.value, father=self.father)

        return dyn

    def _handle_unpack_undefined(self, entry):
        field = fields.StringField(offset=entry.p_offset.value, n=entry.p_filesz.value)

        return field

    def unpack_segment(self, stream, header):
            segment_type = header.p_type.value

            self.logger.debug('found segment type %s' % segment_type)
            self.logger.debug('offset: %d size: %d' % (header.p_offset.value, header.p_filesz.value))

            try:
                callback_name = '_handle_unpack_%s' % segment_type.name
                callback = getattr(self, callback_name)
            except AttributeError:
                callback = self._handle_unpack_undefined

            stream.seek(header.p_offset.value)

            field = callback(header)
            field.vaddr = header.p_vaddr.value  # FIXME: a little hacky
            field.unpack(stream)

            self.value.append(field)

    def unpack(self, stream):
        self.value = []  # reset the entries
        for field_header in self.header:
            self.unpack_segment(stream, field_header)
