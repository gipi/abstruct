#!/usr/bin/env python3
import sys
import os
import logging

from abstruct.executables.elf import ElfFile
from abstruct.executables.elf.enum import (
    ElfSegmentType,
    ElfDynamicTagType,
)

if 'DEBUG' in os.environ:
    logging.basicConfig()
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)


def usage(progname):
    print('usage: %s <elf file>' % progname)
    sys.exit(1)


def dump_header(hdr):
    magic = ''.join(hdr.e_ident.raw.hex())
    print(f'''ELF Header:
  Magic:                             {magic}
  Class:                             {hdr.e_ident.EI_CLASS}
  Data:                              {hdr.e_ident.EI_DATA}
  Version:                           {hdr.e_version}
  OS/ABI:                            {hdr.e_ident.EI_OSABI}
  ABI Version:                       {hdr.e_ident.EI_ABIVERSION}
  Type:                              {hdr.e_type}
  Machine:                           {hdr.e_machine.value}
  Version:                           {hdr.e_ident.EI_VERSION}
  Entry point address:               0x{hdr.e_entry.value:02x}
  Start of program headers:          {hdr.e_phoff} (bytes into file)
  Start of section headers:          {hdr.e_shoff} (bytes into file)
  Flags:                             {hdr.e_flags}
  Size of this header:               {hdr.e_ehsize} (bytes)
  Size of program headers:           {hdr.e_phentsize} (bytes)
  Number of program headers:         {hdr.e_phnum}
  Size of section headers:           {hdr.e_shentsize} (bytes)
  Number of section headers:         {hdr.e_shnum}
  Section header string table index: {hdr.e_shstrndx}''')


def dump_segments(phdr, ph):
    print(f'''Program Headers:
 Type{" ":<36} Offset            VirtAddr   PhysAddr      FileSiz   MemSiz             Flag                Align''')
    for idx, segment in enumerate(phdr.value):
        print(f'''{segment.p_type.value:<40} {segment.p_offset} {segment.p_vaddr.value:08x}-0x{segment.p_vaddr.value + segment.p_memsz.value:08x} 0x{segment.p_paddr.value:08x} 0x{segment.p_filesz.value:08x} 0x{segment.p_memsz.value:08x} {segment.p_flags.value:<30}0x{segment.p_align.value:x}''')
        if segment.p_type.value == ElfSegmentType.PT_INTERP:
            interpreter_path = ph.value[idx].value.decode()
            print(f'''      [Requesting program interpreter: {interpreter_path}]''')


'''
 Section to Segment mapping:
  Segment Sections...
   00     
   01     .interp 
   02     .interp .note.ABI-tag .note.gnu.build-id .gnu.hash .dynsym .dynstr .gnu.version .gnu.version_r .rel.dyn .rel.plt .init .plt .plt.got .text .fini .rodata .eh_frame_hdr .eh_frame 
   03     .init_array .fini_array .dynamic .got .got.plt .data .bss 
   04     .dynamic 
   05     .note.ABI-tag .note.gnu.build-id 
   06     .eh_frame_hdr 
   07     
   08     .init_array .fini_array .dynamic .got
'''


def dump_sections(sh, st):
    print('''Section Headers:
  [Nr] Name               Type                                           Address          Off    Size   ES Flg Lk Inf Al''')
    for idx, section in enumerate(sh.value):
        name = st.get(section.sh_name.value)
        print(f'''  [{idx: >2d}]{name:<20}{section.sh_type.value:<40} {section.sh_addr} {section.sh_offset} 000000 00      0   0  0''')


def dump_dynamic(dyn):
    print(f'''Dynamic section at offset 0x{dyn.offset:x} contains {dyn.n} entries:
  Tag        Type                                          Value''')
    for entry in dyn.value:
        print(f''' {entry.d_tag.value:<35} {entry.d_un}''')


def dump_reloc(relocations, dynamic):
    print(''' Offset     Info    Type            Sym.Value  Sym. Name''')
    for rel in relocations.value:
        print(f'''{rel.r_offset} {rel.r_info.type:<20} {dynamic.get_symbol_name(rel.r_info.sym)}''')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        usage(sys.argv[0])

    path = sys.argv[1]

    elf = ElfFile(path)

    dump_header(elf.header)

    section_table = elf.sections.value[elf.header.e_shstrndx.value] if len(elf.sections.value) > 0 else None
    if elf.sections_header.value:
        dump_sections(elf.sections_header, section_table)

    if elf.segments_header.value:
        dump_segments(elf.segments_header, elf.segments)
    if elf.dynamic:
        dump_dynamic(elf.dynamic)

        needed = elf.dynamic[ElfDynamicTagType.DT_NEEDED]
        print(needed)
        print(elf.dynamic.get(ElfDynamicTagType.DT_NEEDED))


        if ElfDynamicTagType.DT_REL in elf.dynamic:
            rels = elf.dynamic.get(ElfDynamicTagType.DT_REL)
            if rels:
                dump_reloc(rels, elf.dynamic)

        if ElfDynamicTagType.DT_RELA in elf.dynamic:
            rels = elf.dynamic.get(ElfDynamicTagType.DT_RELA)
            if rels:
                dump_reloc(rels, elf.dynamic)
