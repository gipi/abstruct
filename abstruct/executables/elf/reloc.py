from enum import Enum

from . import ElfMachine
from ...core import Chunk, Dependency
from ... import fields
from .fields import Elf_Addr, Elf_Xword, Elf_Sxword


class ElfRelocationInfoField(Elf_Xword):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._arch = Dependency('@ElfFile.header.e_machine')

    def __repr__(self):
        return f'<{self.__class__.__name__}(sym={self.sym}, type={self.type})'

    def get_relocation_type_class(self):
        return {
            ElfMachine.EM_386: ElfRelocationType_i386,
            ElfMachine.EM_X86_64: ElfRelocationType_x64,
        }[self._arch]

    def get_relocation_type(self):
        '''The relocation type is HIGHLY dependent on architecture'''
        return self.get_relocation_type_class()(self.value & self.get_mask())

    def get_shift(self):
        return {
            ElfMachine.EM_386: 8,
            ElfMachine.EM_X86_64: 32,
        }[self._arch]

    def get_mask(self):
        return {
            ElfMachine.EM_386: 0xff,
            ElfMachine.EM_X86_64: 0xffffffff,
        }[self._arch]

    def unpack(self, stream):
        super().unpack(stream)

        self.sym  = self.value >> self.get_shift()
        self.type = self.get_relocation_type()


class ElfRelEntry(Chunk):
    r_offset = Elf_Addr()
    r_info   = ElfRelocationInfoField()


class ElfRelaEntry(ElfRelEntry):
    r_addend = Elf_Sxword()


class ElfRelTable(fields.ArrayField):

    def __init__(self, *args, size=None, **kwargs):
        if size and 'n' in kwargs:  # FIXME: factorize into RealArrayField
            raise ValueError('you cannot pass both n and size')

        if size:
            kwargs['n'] = int(size / ElfRelEntry(father=kwargs['father']).size())

        super().__init__(ElfRelEntry(), *args, **kwargs)


class ElfRelaTable(fields.ArrayField):

    def __init__(self, *args, size=None, **kwargs):
        if size and 'n' in kwargs:  # FIXME: factorize into RealArrayField
            raise ValueError('you cannot pass both n and size')

        if size:
            kwargs['n'] = int(size / ElfRelaEntry(father=kwargs['father']).size())

        super().__init__(ElfRelaEntry(), *args, **kwargs)


class ElfRelocationType_i386(Enum):
    R_386_NONE = 0
    R_386_32   = 1
    R_386_PC32 = 2
    R_386_GOT32 = 3
    R_386_PLT32 = 4
    R_386_COPY  = 5
    R_386_GLOB_DAT = 6
    R_386_JMP_SLOT = 7
    R_386_RELATIVE = 8
    R_386_GOTOFF   = 9
    R_386_GOTPC    = 10
    R_386_32PLT    = 11
    R_386_16       = 20
    R_386_PC16     = 21
    R_386_8        = 22
    R_386_PC8      = 23
    R_386_SIZE32   = 38


class ElfRelocationType_x64(Enum):
    """
    Source: <https://docs.oracle.com/cd/E19120-01/open.solaris/819-0690/chapter7-2/index.html>
            <https://www.cs.dartmouth.edu/~sergey/cs258/2009/817-1984.pdf>

    But probably the best is to read directly from the elf.h of your libc's source code.
    """
    R_AMD64_NONE = 0
    R_AMD64_64 = 1
    R_AMD64_PC32 = 2
    R_AMD64_GOT32 = 3
    R_AMD64_PLT32 = 4
    R_AMD64_COPY = 5
    R_AMD64_GLOB_DAT = 6
    R_AMD64_JUMP_SLOT = 7
    R_AMD64_RELATIVE = 8
    R_AMD64_GOTPCREL = 9
    R_AMD64_32 = 10
    R_AMD64_32S = 11
    R_AMD64_16 = 12
    R_AMD64_PC16 = 13
    R_AMD64_8 = 14
    R_AMD64_PC8 = 15
    # Thread-Local Storage Relocation Types
    R_AMD64_DPTMOD64 = 16
    R_AMD64_DTPOFF64 = 17
    R_AMD64_TPOFF64 = 18
    R_AMD64_TLSGD = 19
    R_AMD64_TLSLD = 20
    R_AMD64_DTPOFF32 = 21
    R_AMD64_GOTTPOFF = 22
    R_AMD64_TPOFF32 = 23
    # end TLS ###
    R_AMD64_PC64 = 24
    R_AMD64_GOTOFF64 = 25
    R_AMD64_GOTPC32 = 26
    R_X86_64_GOT64 = 27
    R_X86_64_GOTPCREL64 = 28
    R_X86_64_GOTPC64 = 29
    R_X86_64_GOTPLT64 = 30
    R_X86_64_PLTOFF64 = 31
    R_AMD64_SIZE32 = 32
    R_AMD64_SIZE64 = 33
    R_X86_64_GOTPC32_TLSDESC = 34
    R_X86_64_TLSDESC_CALL = 35
    R_X86_64_TLSDESC = 36
    R_X86_64_IRELATIVE = 37
    R_X86_64_RELATIVE64 = 38
    R_X86_64_GOTPCRELX = 41
    R_X86_64_REX_GOTPCRELX = 42
