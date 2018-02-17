import sys
from abstruct.elf import ElfFile, ElfHeader


elf = ElfFile()

sys.stdout.write(elf.pack())
