'''
This module helps to encode/decode machine instructions

Some examples here: <https://www.capstone-engine.org/lang_python.html>.
'''
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

from . import SectionHeader, ElfMachine

_map = {
    ElfMachine.EM_386: (CS_ARCH_X86, CS_MODE_32),
}


def disasm(code, arch, mode, start=0, detail: bool = True):
    md = Cs(arch, mode)
    md.detail = detail

    for _ in md.disasm(code, start):
        yield _


def _disasm(section_header: SectionHeader, arch=None, mode=None, start: int = 0):
    elf = section_header.father.father
    arch, mode = _map[elf.header.e_machine.value] if arch is None or mode is None else (arch, mode)

    s_header, section = elf.get_section_by_address(section_header.sh_addr.value)

    return disasm(section.value, arch, mode, start=start)
