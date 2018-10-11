# Design

There are two pretty distinct phases for a format:

 - unpacking: transform raw data in attributes
 - packing: transforming attributes in raw data

The problems arise when we modify attributes and want that other attributes
that depend on those are updated or not by default.

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
explicitely set that passes that to the fields of interest: internally the
container class will create an hidden attribute to which the dependent
parameters will refer to. This although generate a problem of updating
such field. In this way we don't have to think about absolute and relative
dependencies.

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
