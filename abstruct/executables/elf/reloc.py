from ...core import Chunk
from ... import fields
from .fields import Elf_Addr, ElfRelocationInfoField


class ElfRelEntry(Chunk):
    r_offset = Elf_Addr()
    r_info   = ElfRelocationInfoField()


class ElfRelocationTable(fields.RealArrayField):

    def __init__(self, *args, size=None, **kwargs):
        if size and 'n' in kwargs:  # FIXME: factorize into RealArrayField
            raise ValueError('you cannot pass both n and size')

        if size:
            kwargs['n'] = int(size / ElfRelEntry(father=kwargs['father']).size())

        super().__init__(ElfRelEntry, *args, **kwargs)
