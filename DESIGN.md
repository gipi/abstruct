# Design

This library scope is to parse and to build binary file format starting from an high
level description represented by a python class, in the same way Django models
abstract away the database layer and allow to forget about underlying structures.

There are two pretty distinct phases for a format:

 - unpacking: transform raw data in attributes
 - packing: transforming attributes in raw data

the terminology is borrowed from the ``struct`` module.

## Chunks

Roughly speaking a file format is composed of several **chunks** of bytes: i.e.
a countigous stream of bytes identified by two particular attributes **offset**
and **size**. In real format is possible that a chunk determines also another distinct
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

## Offset

## Examples

```
,----- fixed size ---.
[header][padding][CRC]
```

here we have a chunk of fixed size with a padding that depends on it by an algebraic
relation with the size of the remanaing fields.
