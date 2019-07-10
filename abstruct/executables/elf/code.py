'''
This module helps to encode/decode machine instructions

Some examples here: <https://www.capstone-engine.org/lang_python.html>.
'''
from capstone import Cs, CS_ARCH_X86, CS_MODE_32


def disasm(code, arch, mode, start=0):
    md = Cs(arch, mode)

    for _ in md.disasm(code, start):
        yield _

