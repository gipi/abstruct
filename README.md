# Abstruct

The ``struct`` module on steroid.

![travis build status](https://travis-ci.org/gipi/abstruct.svg?branch=master)

**This is a work in progress!!**

I want to create a module able to ``pack()/unpack()`` generic file format
described by using standard python classes syntax (the inspiration come from
the way Django models work).

This because I need a module ables to not only to read but also to modify and to write
``ELF`` files and it seems that there are not module for this.

The API will be change very heavily in future, I'm in the design phase. It uses python3.

## Roadmap

 - [ ] add common file formats
   - [ ] PNG
     - [x] IHDR
     - [x] PLTE
     - [x] IDAT
   - [ ] JPEG
   - [ ] ZIP
   - [ ] PDF
   - [ ] ELF
     - [x] use endianess indicated in ``header.e_ident.EI_DATA`` for all the fields
     - [x] use word size indicated by ``header.e_ident.EI_CLASS`` for the fields involved
     - [x] read ``ELF`` header
     - [x] read ``ELF`` sections header
     - [ ] read ``ELF`` sections data
     - [x] read ``ELF`` segments header
     - [ ] read ``ELF`` segments data
     - [ ] resolve architecture dependent data
       - [ ] i386
       - [ ] x86_64
       - [ ] mips
       - [ ] arm
 - [ ] Add uncommon formats
   - [ ] QR-Code (this is the encoding of binary data using images, the opposite of a format like ``PNG``)
 - [ ] core functionalities
   - [ ] add check for Field and Chunk
   - [ ] resolve dependencies between fields
     - [ ] absolute reference (``elf_header.e_shnum``)
     - [ ] relative reference (``..field.another_field``)
     - [ ] using operators (``section.index in sections where sh_type == SHT_STRTAB``)
   - [ ] manage offsets
   - [ ] write

## Example

This below is an example for an ``ELF`` header

```python
from abstruct.core import Chunk
from abstruct import fields
from abstruct.executables.elf import fields as elf_fields
from abstruct.executables.elf.enum import (
    ElfEIClass,
    ElfEIData,
    ElfOsABI,
    ElfType,
    ElfMachine,
    ElfVersion,
)


class ElfIdent(Chunk):
    EI_MAG0 = fields.StructField('c', default=b'\x7f')
    EI_MAG1 = fields.StructField('c', default=b'E')
    EI_MAG2    = fields.StructField('c', default=b'L')
    EI_MAG3    = fields.StructField('c', default=b'F')
    EI_CLASS   = fields.StructField('B', enum=ElfEIClass, default=ElfEIClass.ELFCLASS32)  # determines the architecture
    EI_DATA    = fields.StructField('B', enum=ElfEIData, default=ElfEIData.ELFDATA2LSB)  # determines the endianess of the binary data
    EI_VERSION = fields.StructField('B', default=1)  # always 1
    EI_OSABI   = fields.StructField('B', enum=ElfOsABI, default=ElfOsABI.ELFOSABI_GNU)
    EI_ABIVERSION = fields.StructField('B')
    EI_PAD     = fields.StringField(7)


class ElfHeader(Chunk):
    e_ident     = fields.ElfIdentField()
    e_type      = elf_fields.Elf_Half(enum=ElfType, default=ElfType.ET_EXEC)
    e_machine   = elf_fields.Elf_Half(enum=ElfMachine, default=ElfMachine.EM_386)
    e_version   = elf_fields.Elf_Word(enum=ElfVersion, default=ElfVersion.EV_CURRENT)
    e_entry     = elf_fields.Elf_Addr()
    e_phoff     = elf_fields.Elf_Off()
    e_shoff     = elf_fields.Elf_Off()
    e_flags     = elf_fields.Elf_Word()
    e_ehsize    = elf_fields.Elf_Half(equals_to=Dependency('size'))
    e_phentsize = elf_fields.Elf_Half()
    e_phnum     = elf_fields.Elf_Half()
    e_shentsize = elf_fields.Elf_Half()
    e_shnum     = elf_fields.Elf_Half()
    e_shstrndx  = elf_fields.Elf_Half()


header = ElfHeader('/bin/ls')
print(header.e_entry.value) # will print the value associated with the field
```

