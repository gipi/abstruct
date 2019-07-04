'''
# Elf format

Executable and Linkage Format is a file format vastly used in the *nix world.

'''
from enum import Enum

from ... import fields
from ...core import Chunk
"""
From ELF: Executable and Linkable Format page 8, Data types


"""


# FIXME: the endianess depens on EI_DATA

class ElfEIClass(Enum):
    ELFCLASSNONE = 0
    ELFCLASS32   = 1
    ELFCLASS64   = 2


class ElfEIData(Enum):
    ELFDATANONE = 0
    ELFDATA2LSB = 1
    ELFDATA2MSB = 2


class ElfIdent(Chunk):
    EI_MAG0 = fields.StructField('c', default=b'\x7f')
    EI_MAG1 = fields.StructField('c', default=b'E')
    EI_MAG2    = fields.StructField('c', default=b'L')
    EI_MAG3    = fields.StructField('c', default=b'F')
    EI_CLASS   = fields.StructField('B', default=ElfEIClass.ELFCLASS32.value) # determines the architecture
    EI_DATA    = fields.StructField('B', default=ElfEIData.ELFDATA2LSB.value) # determines the endianess of the binary data
    EI_VERSION = fields.StructField('B', default=1) # always 1
    EI_PAD     = fields.StringField(9)


class ElfSegmentType(Enum):
    PT_NULL = 0
    PT_LOAD = 1
    PT_DYNAMIC = 2
    PT_INTERP  = 3
    PT_NOTE    = 4
    PT_SHLIB   = 5
    PT_PHDR    = 6
    PT_LOPROC  = 0x70000000
    PT_HIPROC  = 0x7fffffff


# TODO: create BoolFromDependency that use the EI_CLASS from the ELF header
#       and generates the endianess to pass via the little_endian parameter.
class RealELF_Addr(fields.StructField):
    '''Wrapper for the fundamental datatype of the ELF format'''
    def __init__(self, **kwargs):
        super().__init__('I')


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

    def pack(self, stream=None):
        '''TODO: we have to update also the corresponding header entries'''
        for field in self.header:
            logger.debug('pack()()()')

    def unpack(self, stream):
        self.value = [] # reset the entries
        for field in self.header:
            section_type = field.sh_type.value
            logger.debug('found section type %d' % section_type)


class ELFSectionsField(fields.Field):
    real = RealELFSectionsField

