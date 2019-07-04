# Design

This library scope is to parse and to build binary file formats starting from an high
level description represented by a python class, in the same way Django models
abstracts away the database layer and allows to forget about underlying structures.

There are two pretty distinct actions possible with an instance created with this module:

 - unpacking: transform raw data in attributes
 - packing: transforming attributes in raw data

the terminology is borrowed from the ``struct`` module.

## Chunks and fields

Roughly speaking a file format is composed of several **chunks** of bytes: i.e.
a **countigous** stream of bytes identified by two particular attributes, the **offset**
and the **size**. When a chunk is directly representable as a byte-like value
is it a field.

It's very important that we set a chunk to be "without holes" in order to be
easier to manage, obviously not all formats are kind enough to behave like that,
think of the ``ELF`` format with sections and segments having their headers
intermixed, but we try to follow as much as possible this idea.

A chunk can have its attribute depending on other attributes of other chunks
at some hierarchical level in the containing chunk (hopefully in a sane way),
think at the ``ELF`` format that indicates in the entries of the section header the offset
for the data for a given segment (and also the type of section). This is particular
important when the attributes are size or the offset that tightly connected
to the pack()/unpacking() routines.

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

## Stream

Since in general case a format needs to read data in random position following
the offsets the pack()/unpack() methods need an explicit stream to be passed
as an argument.

The stream MUST implement the usual API for the usual stream that you can encounter
but also a save()/restore() methods that manage the offset of the stream.

## APIs

We'll try to describe what are the attributes and methods available an high
level description

### ``size``

It indicates the internal size in bytes of the data contained in the chunk/field.
When you unpack/pack an instance, the stream will be advanced by this amount.

If not indicated explicitely the chunk knows internally its own size

### ``offset``

It indicates the offset from the main container of the chunk.
It is used by the parent during the unpack/pack process to
seek the stream to the actual position, but the field/chunk itself
it's not involved with the seeking.

TBD: probably is most useful to take the offset from the direct
parent!

### ``value``

It indicates the high level representation for the data, for now it is
present only in a field.

### ``data``

This attribute returns the raw data bytes of a chunk.

TDB: we cache it, we recalculate it and propagate the changes?

TO BE IMPLEMENTED

### ``compliant``

Attribute that indicates how the chunk is going to handle dependencies,
i.e. enforcing in a way that the format remains compliant or allowing
to misbehave

TO BE IMPLEMENTED

### ``unpack()``

It's the simpler and straightforwad method: it reads the data and
set the offsets and sizes accordingly.

If we unpack we should forget any possible dependencies and simply put the
raw data; it would be necessary a method to check/fix discordant values
(another problem would be, what values has priority).

### ``pack()``

Here is a little complicated because one possibility is that we set the data
in such a way that the resulting raw data is not compliant, or we want to
forget all, some dependencies.

The main problem comes from the dependencies: offsets and sizes of a chunk that depend
on the value explicitely indicated by a previous field indicates that
the packing process needs a relayouting algorithm in multiple steps.

Think it in this way:

 - trigger the pack() from the main instance
 - the main instance recursively set the ON_PACKING phase for all the subchunks
 - the main instance call pack() for all the subfield
   - if a subchunk does not depend on nothing set it phase as PACKED
   - repeat until all the subchunk are PACKED

We must return the byte representation of the given chunk, if a stream is passed
it is used to store the data.

If we pack we should can choose between maintaining the sanity of the format
updating with respect to the constraints of the format or pack as the fields
are in the actual instance.

## Default

Are we expecting that a new created instance has already values
that make sense or we want all set to None and then, when we need
a looking-right instance, an option for pack, or a method of its own?

The parameters passed to build the default value, must be retained?


## Examples

```
,----- fixed size ---.
[header][padding][CRC]
```

here we have a chunk of fixed size with a padding that depends on it by an algebraic
relation with the size of the remanaing fields.

