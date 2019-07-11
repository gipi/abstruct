from ...core import Chunk
from ... import fields
from .fields import Elf_Addr, Elf_Word


class ElfRelEntry(Chunk):
    r_offset = Elf_Addr()
    r_info   = Elf_Word()


class RelocationTable(fields.RealArrayField):
    def __init__(self, *args, **kwargs):
        super().__init__(ElfRelEntry, *args, **kwargs)

