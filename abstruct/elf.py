from .core import *
from . import fields
from .properties import Offset



class ElfHeader(Chunk):
    e_ident     = fields.StringField(16, default=b'\x7fELF\x01\x01\x01') # FIXME: there are sub-fields
    e_type      = fields.StructField('H', default=0x2) # ET_EXEC
    e_machine   = fields.StructField('H', default=0x3) # EM_386
    e_version   = fields.StructField('I', default=0x1) # Version 1
    e_entry     = fields.StructField('I')
    e_phoff     = fields.StructField('I')
    e_shoff     = fields.StructField('I')
    e_flags     = fields.StructField('I')
    e_ehsize    = fields.StructField('H')
    e_phentsize = fields.StructField('H')
    e_phnum     = fields.StructField('H')
    e_shentsize = fields.StructField('H')
    e_shnum     = fields.StructField('H')
    e_shstrndx  = fields.StructField('H')

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.data = None

    def unpack(self, stream):
        super().unpack(stream)

        # since can be present other fields at this
        # offset that we need to unpack, we save
        # the offset
        stream.save()

        # seek to the data we need
        stream.seek(self.sh_offset.value)
        # read it
        self.data = stream.read(self.sh_size.value)

        # and and restore the saved offset
        stream.restore()

class ElfFile(Chunk):
        elf_header = fields.ElfHeaderField()
        sections   = fields.ArrayField(SectionHeader, n=Dependency('elf_header.e_shnum'), offset=Offset('elf_header.e_shoff'))

