'''
# Elf format

Executable and Linkage Format is a file format vastly used in the *nix world.

'''
import logging

from ... import fields
from ...core import Chunk
from .enum import (
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


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ElfIdent(Chunk):
    EI_MAG0 = fields.StructField('c', default=b'\x7f')
    EI_MAG1 = fields.StructField('c', default=b'E')
    EI_MAG2    = fields.StructField('c', default=b'L')
    EI_MAG3    = fields.StructField('c', default=b'F')
    EI_CLASS   = fields.StructField('B', enum=ElfEIClass, default=ElfEIClass.ELFCLASS32)  # determines the architecture
    EI_DATA    = fields.StructField('B', enum=ElfEIData, default=ElfEIData.ELFDATA2LSB)  # determines the endianess of the binary data
    EI_VERSION = fields.StructField('B', default=1)  # always 1
    EI_OSABI   = fields.StructField('B', enum=ElfOsABI, default=ElfOsABI.ELFOSABI_GNU)
    EI_ABIVERSION = fields.StructField('B')
    EI_PAD     = fields.StringField(7)


# TODO: create BoolFromDependency that use the EI_CLASS from the ELF header
#       and generates the endianess to pass via the little_endian parameter.
class RealElf_DataType(fields.RealStructField):
    '''Wrapper for all the datatype that resolves internally to the EI_CLASS'''

    def __init__(self, **kwargs):
        self._elf_class = Dependency('elf_header.e_ident.EI_CLASS')
        kwargs['endianess'] = Dependency('elf_header.e_ident.EI_DATA')
        super().__init__('I', **kwargs)

    def get_format(self):
        return '%s%s' % (
            '<' if self.endianess == ElfEIData.ELFDATA2LSB else '>',
            self.MAP_CLASS_TYPE[self._elf_class],
        )


class RealElf_Addr(RealElf_DataType):
    '''Unsigned program address'''

    MAP_CLASS_TYPE = {
        ElfEIClass.ELFCLASS32: 'I',
        ElfEIClass.ELFCLASS64: 'Q',
    }


class RealElf_Off(RealElf_DataType):
    '''Unsigned file offset'''

    MAP_CLASS_TYPE = {
        ElfEIClass.ELFCLASS32: 'I',
        ElfEIClass.ELFCLASS64: 'Q',
    }


class RealElf_Sword(RealElf_DataType):
    '''Wrapper for the fundamental datatype of the ELF format'''

    MAP_CLASS_TYPE = {
        ElfEIClass.ELFCLASS32: 'I',
        ElfEIClass.ELFCLASS64: 'I',
    }


class RealElf_Xword(RealElf_DataType):
    ''''''

    MAP_CLASS_TYPE = {
        ElfEIClass.ELFCLASS32: 'I',
        ElfEIClass.ELFCLASS64: 'Q',
    }


class RealElf_Sxword(RealElf_DataType):

    MAP_CLASS_TYPE = {
        ElfEIClass.ELFCLASS32: 'Q',
        ElfEIClass.ELFCLASS64: 'Q',
    }


class RealElf_Word(RealElf_DataType):
    '''Wrapper for the fundamental datatype of the ELF format'''

    MAP_CLASS_TYPE = {
        ElfEIClass.ELFCLASS32: 'I',
        ElfEIClass.ELFCLASS64: 'I',
    }


class RealElf_Half(RealElf_DataType):
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


class Elf_Addr(fields.StructField):
    real = RealElf_Addr


class Elf_Off(fields.StructField):
    real = RealElf_Off


class Elf_Sword(fields.Field):
    real = RealElf_Sword


class Elf_Xword(fields.Field):
    real = RealElf_Xword


class Elf_Word(fields.Field):
    real = RealElf_Word


class Elf_Sxword(fields.Field):
    real = RealElf_Sxword


class Elf_Half(fields.Field):
    real = RealElf_Half


# TODO: maybe better subclass of Chunk with ArrayField as unique element?
class RealSectionStringTable(fields.RealField):
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


class SectionStringTable(fields.Field):
    real = RealSectionStringTable


class RealSymbolInfoField(fields.RealStructField):
    '''
#define ELF32_ST_BIND(i) (( i ) >> 4)
#define ELF32_ST_TYPE(i) (( i ) & 0xf)
#define ELF32_ST_INFO(b, t) ((( b ) << 4) + (( t ) & 0xf))
    '''

    def __init__(self, *args, **kwargs):
        super().__init__('B', *args, **kwargs)

    def __str__(self):
        return '<Info(%s,%s)>' % (self.bind, self.type)

    def unpack(self, stream):
        '''it reads and then split the values in bind and type'''
        super().unpack(stream)
        self.bind = ElfSymbolBindType(self.value >> 4)
        self.type = ElfSymbolType(self.value & 0x0f)


class SymbolInfoField(fields.StructField):
    real = RealSymbolInfoField


class SymbolTableEntry(Chunk):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._elf_class = Dependency('elf_header.e_ident.EI_CLASS')

    def get_fields(self):  # TODO: factorize this code in more pythonic way
        original_fields = super().get_fields()
        # FIXME: here we need to call resolve() by ourself since it's not a field
        if self._elf_class.resolve(self) == ElfEIClass.ELFCLASS32:
            return original_fields

        ORDERING_64 = [
            'st_name',
            'st_info',
            'st_other',
            'st_shndx',
            'st_value',
            'st_size',
        ]
        modified_fields = []
        # FIXME: this is shit
        for name in ORDERING_64:
            for _ in original_fields:
                if _[0] == name:
                    modified_fields.append(_)
                    break

        return modified_fields

    st_name  = Elf_Word()
    st_value = Elf_Addr()
    st_size  = Elf_Xword()
    st_info  = SymbolInfoField()
    st_other = fields.StringField(0x01)
    st_shndx = Elf_Half()


class SymbolTable(fields.RealArrayField):

    def __init__(self, *args, **kwargs):
        super().__init__(SymbolTableEntry, *args, **kwargs)


class DynamicEntry(Chunk):
    d_tag = Elf_Sxword(enum=ElfDynamicTagType)
    d_un  = Elf_Xword()  # FIXME: create UnionField


class RealElfDynamicSegmentField(fields.RealArrayField):

    def __init__(self, *args, size=None, father=None, **kwargs):
        super().__init__(DynamicEntry, *args, n=int(size / DynamicEntry(father=father).size()), father=father, **kwargs)


class RealELFSectionsField(fields.RealField):
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
            logger.debug('pack()()()')

    def unpack(self, stream):
        self.value = []  # reset the entries
        for field in self.header:
            section_type = field.sh_type.value
            logger.debug('found section type %s' % section_type)
            logger.debug('offset: %d size: %d' % (field.sh_offset.value, field.sh_size.value))

            if section_type == ElfSectionType.SHT_STRTAB:
                logger.debug('unpacking string table')
                # we need to unpack at most sh_size bytes
                stream.seek(field.sh_offset.value)
                section = RealSectionStringTable(size=field.sh_size.value)
                section.unpack(stream)
                self.value.append(section)
                print(section.value)
            elif section_type == ElfSectionType.SHT_SYMTAB:
                table_size = field.sh_size.value
                logger.debug('unpacking symbol table')
                n = int(table_size / SymbolTableEntry(father=self).size())  # FIXME: create Dependency w algebraic operation
                logger.debug(' with %d entries' % n)

                stream.seek(field.sh_offset.value)

                section = SymbolTable(n=n, father=self)
                section.unpack(stream)

                self.value.append(section)
            elif section_type == ElfSectionType.SHT_DYNSYM:
                table_size = field.sh_size.value
                logger.debug('unpacking dynamic symbol table')
                n = int(table_size / SymbolTableEntry(father=self).size())  # FIXME: create Dependency w algebraic operation
                logger.debug(' with %d entries' % n)

                stream.seek(field.sh_offset.value)

                section = SymbolTable(n=n, father=self)
                section.unpack(stream)

                self.value.append(section)
            elif section_type == ElfSectionType.SHT_REL:
                from .reloc import RelocationTable
                from .reloc import ElfRelEntry
                table_size = field.sh_size.value

                logger.debug('unpacking relocation table')
                n = int(table_size / ElfRelEntry(father=self).size())  # FIXME: create Dependency w algebraic operation
                logger.debug(' with %d entries' % n)

                stream.seek(field.sh_offset.value)

                section = RelocationTable(n=n, father=self)
                section.unpack(stream)

                self.value.append(section)
                print(section)
            else:
                logger.debug('unpacking unhandled data of type %s' % section_type)
                stream.seek(field.sh_offset.value)
                section = fields.RealStringField(field.sh_size.value)
                section.unpack(stream)

                self.value.append(section)


class RealELFSegmentsField(fields.RealField):
    '''Handles the data pointed by an entry of the program header
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
            logger.debug('pack()()()')

    def _handle_unpack_PT_PHDR(self, entry):
        '''It handles the header, simply using a StringField'''
        field = fields.RealStringField(entry.p_filesz.value)

        return field

    def _handle_unpack_PT_INTERP(self, entry):
        interp = ELFInterpol(offset=entry.p_offset.value, size=entry.p_filesz.value)

        return interp

    def _handle_unpack_PT_DYNAMIC(self, entry):
        dyn = RealElfDynamicSegmentField(offset=entry.p_offset.value, size=entry.p_filesz.value, father=self.father)

        return dyn

    def _handle_unpack_undefined(self, entry):
        field = fields.RealStringField(offset=entry.p_offset.value, size=entry.p_filesz.value)

        return field

    def unpack_segment(self, stream, header):
            segment_type = header.p_type.value

            logger.debug('found segment type %s' % segment_type)
            logger.debug('offset: %d size: %d' % (header.p_offset.value, header.p_filesz.value))

            callback_name = '_handle_unpack_%s' % segment_type.name
            try:
                callback = getattr(self, callback_name)
            except AttributeError:
                callback = self._handle_unpack_undefined

            stream.seek(header.p_offset.value)

            field = callback(header)
            field.unpack(stream)

            self.value.append(field)

    def unpack(self, stream):
        self.value = []  # reset the entries
        for field_header in self.header:
            self.unpack_segment(stream, field_header)


class ELFSectionsField(fields.Field):
    real = RealELFSectionsField


class ELFSegmentsField(fields.Field):
    real = RealELFSegmentsField
