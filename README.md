# Abstruct

![travis build status](https://travis-ci.org/gipi/abstruct.svg?branch=master)

**This is a work in progress!!**

I want to create a module able to ``pack()/unpack()`` generic file format
described by using standard python classes syntax (this is very high inspired
by the way Django model works).

This because a need a module ables to not only read but also modify and write
``ELF`` files and seems that there are not module for this.

The API will be change very heavily in future. It uses python3.

## Roadmap

 - [ ] add common file formats
   - [ ] PNG
   - [ ] JPEG
   - [ ] ZIP
   - [ ] PDF
   - [ ] ELF
     - [x] read ``ELF`` header
     - [ ] read ``ELF`` sections and segments
 - [ ] add check for Field and Chunk
 - [ ] resolve dependencies between fields
   - [ ] absolute reference (``elf_header.e_shnum``)
   - [ ] relative reference (``..field.another_field``)
   - [ ] using operators (``section.index in sections where sh_type == SHT_STRTAB``)
 - [ ] manage offsets
 - [ ] write

## Example

This below is an example for 32 bits ``ELF`` header.

```python
from abstruct.core import Chunk
from abstruct.fields import StringField, StructField

class Elf32Header(Chunk):
    e_ident     = StringField(16, default=b'\x7fELF\x01\x01\x01')
    e_type      = StructField('H', default=0x2) # ET_EXEC
    e_machine   = StructField('H', default=0x3) # EM_386
    e_version   = StructField('I', default=0x1) # Version 1
    e_entry     = StructField('I')
    e_phoff     = StructField('I')
    e_shoff     = StructField('I')
    e_flags     = StructField('I')
    e_ehsize    = StructField('H')
    e_phentsize = StructField('H')
    e_phnum     = StructField('H')
    e_shentsize = StructField('H')
    e_shnum     = StructField('H')
    e_shstrndx  = StructField('H')

header = Elf32Header('/bin/ls') # NOTE: it must be a 32bit ELF
print(header.e_entry.value) # will print the value associated with the field
```
