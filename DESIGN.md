# Design

This library scope is to parse and to build binary file formats starting from an high
level description represented by a python class, in the same way Django models
abstracts away the database layer and allows to forget about underlying structures.

There are two pretty distinct phases for a format:

 - unpacking: transform raw data in attributes
 - packing: transforming attributes in raw data

the terminology is borrowed from the ``struct`` module.

## Chunks and fields

Roughly speaking a file format is composed of several **chunks** of bytes: i.e.
a countigous stream of bytes identified by two particular attributes **offset**
and **size**. When a chunk is directly representable as a byte-like value
is it a field.


In real format is possible that a chunk determines also another distinct
chunk at some offset determined by a field in it (think about the ELF section header).

A problems arises when we have attributes that depend on other attributes, like a
field that determines the size of the following field in the format description:
imagine a format like the following

```
class FormatA(Chunk):
    class Dependencies:
        relations = [
            ('subchunk_size', 'subchunk.size'),
        ]
    magic = fields.StringField(default=b'\xca\xfe\xba\xbe')
    subchunk_size  = fields.StructField('I')
    subchunk = fields.SubChunkField()
```

in the unpacking we need to have unpacked the ``subchunk`` chunk before we can determine
the size to put into the ``subchunk_size`` field.

**N.B.:** here we can see that the dependency is one-way since it's a little tricky
to decide what to do if we change the size

Moreover from a single field can depend more than one field (for example the field
``EI_DATA`` in the ``ELF`` header determines the endianess of the file format for the
given ``ELF`` file).

## Unpack

If we unpack we should forget any possible dependencies and simply put the
raw data; it would be necessary a method to check/fix discordant values
(another problem would be, what values has priority).

## Pack

If we pack

## Default

Are we expecting that a new created instance has already values
that make sense or we want all set to None and then, when we need
a looking-right instance, an option for pack, or a method of its own?

## Dependencies

Field subclasses automagically resolve attributes set to Dependency

BTW there are fields that have dependencies that should be updated also in
inverse

Probably the best solution is to use a Meta class with dependency
explicitely set that passes that to the fields of interest

For example, the ``ELF`` format has an header that indicates in the
field named ``e_shoff`` at what offset the section header table is;
obviously the offset of the ArrayField containing the section header ``Chunk``s
must depends on this field and the other way around: if I set explicitely the
offset of this array, the field corresponding must update.

Another question is, if this is possible, I mean, in the ``ELF`` specification
I don't see any indication of a minimal distance between parts, so probably I can put
this where I want.

Obviously if we want to use the library as a tool to create files without
enforcing dependencies (think of fuzzing for example) we need an attribute assigned
to the chunk that set recursively in all its children off the dependencies.

## Offset

## Examples

```
,----- fixed size ---.
[header][padding][CRC]
```

here we have a chunk of fixed size with a padding that depends on it by an algebraic
relation with the size of the remanaing fields.

## API

Each ``Chunk`` has the following

 - pack()
 - unpack()

instead ``Field`` subclasses have the attribute

 - ``value`` that gives
