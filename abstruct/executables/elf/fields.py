'''
# Elf format

Executable and Linkage Format is a file format vastly used in the *nix world.

'''
from enum import Enum
import logging

from ... import fields
from ...core import Chunk
from .enum import *


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# FIXME: the endianess depens on EI_DATA


class ElfIdent(Chunk):
    EI_MAG0 = fields.StructField('c', default=b'\x7f')
    EI_MAG1 = fields.StructField('c', default=b'E')
    EI_MAG2    = fields.StructField('c', default=b'L')
    EI_MAG3    = fields.StructField('c', default=b'F')
    EI_CLASS   = fields.StructField('B', default=ElfEIClass.ELFCLASS32.value) # determines the architecture
    EI_DATA    = fields.StructField('B', default=ElfEIData.ELFDATA2LSB.value) # determines the endianess of the binary data
    EI_VERSION = fields.StructField('B', default=1) # always 1
    EI_PAD     = fields.StringField(9)


# TODO: create BoolFromDependency that use the EI_CLASS from the ELF header
#       and generates the endianess to pass via the little_endian parameter.
class RealElf_Addr(fields.RealStructField):
    '''Wrapper for the fundamental datatype of the ELF format'''
    def __init__(self, **kwargs):
        super().__init__('I', **kwargs)


class RealElf_Sword(fields.RealStructField):
    '''Wrapper for the fundamental datatype of the ELF format'''
    def __init__(self, **kwargs):
        super().__init__('I', **kwargs)


class RealElf_Word(fields.RealStructField):
    '''Wrapper for the fundamental datatype of the ELF format'''
    def __init__(self, **kwargs):
        super().__init__('I', **kwargs)


class RealElf_Half(fields.RealStructField):
    '''Wrapper for the fundamental datatype of the ELF format'''
    def __init__(self, **kwargs):
        super().__init__('H', **kwargs)


class RealElf_Off(fields.RealStructField):
    '''Wrapper for the fundamental datatype of the ELF format'''
    def __init__(self, **kwargs):
        super().__init__('I', **kwargs)


class ELFInterpol(Chunk): # TODO: use StringField
    def __init__(self, *args, size=None, **kwargs):
        super().__init__(*args, **kwargs)

        self._size = size

    def unpack(self, stream):
        self.value = stream.read(self._size)

class Elf_Sword(fields.Field):
    real = RealElf_Sword


class Elf_Word(fields.Field):
    real = RealElf_Word


class Elf_Half(fields.Field):
    real = RealElf_Half


class Elf_Addr(fields.Field):
    real = RealElf_Addr


from .reloc import RelocationTable
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


class SymbolTableEntry(Chunk):
    st_name  = Elf_Word()
    st_value = Elf_Addr()
    st_size  = Elf_Word()
    st_info  = fields.StringField(0x01)
    st_other = fields.StringField(0x01)
    st_shndx = Elf_Half()


class SymbolTable(fields.RealArrayField):
    def __init__(self, *args, **kwargs):
        super().__init__(SymbolTableEntry, *args, **kwargs)


class RealELFSectionsField(fields.RealField):
    '''Handles the data pointed by an entry of the Section header
    TODO: how do entry from this and the corresponding header behave wrt each other?
          if we remove the header, we remove the entry and vice versa?
    '''
    def __init__(self, header, *args, **kwargs):
        '''Use the header parameter to get the entries needed'''
        super().__init__(*args, **kwargs)
        self.header = header # this MUST be a Dependency

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
        self.value = [] # reset the entries
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
                n = int(table_size/SymbolTableEntry().size()) # FIXME: create Dependency w algebraic operation
                logger.debug(' with %d entries' % n)

                stream.seek(field.sh_offset.value)

                section = SymbolTable(n=n)
                section.unpack(stream)

                self.value.append(section)
                print(section)
            elif section_type == ElfSectionType.SHT_REL:
                from .reloc import ElfRelEntry
                table_size = field.sh_size.value

                logger.debug('unpacking relocation table')
                n = int(table_size/ElfRelEntry().size()) # FIXME: create Dependency w algebraic operation
                logger.debug(' with %d entries' % n)

                stream.seek(field.sh_offset.value)

                section = RelocationTable(n=n)
                section.unpack(stream)

                self.value.append(section)
                print(section)
            else:
                logger.debug('unpacking unhandled data')
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
        self.header = header # this MUST be a Dependency

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
        self.value = [] # reset the entries
        for field in self.header:
            segment_type = field.p_type.value
            logger.debug('found section type %d' % segment_type)
            logger.debug('offset: %d size: %d' % (field.p_offset.value, field.p_filesz.value))

            if segment_type == ElfSegmentType.PT_INTERP.value:
                interp = ELFInterpol(offset=field.p_offset.value, size=field.p_filesz.value)

                real_offset = field.p_offset
                interp.unpack(stream)
                # we don't need to set the field's offset
                print('>>>', interp.value)
            else:
                logger.debug('unpacking unhandled data')
                stream.seek(field.p_offset.value)
                section = fields.RealStringField(field.p_filesz.value)
                section.unpack(stream)

                self.value.append(section)

class ELFSectionsField(fields.Field):
    real = RealELFSectionsField

class ELFSegmentsField(fields.Field):
    real = RealELFSegmentsField

