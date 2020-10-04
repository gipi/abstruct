"""
# Abstruct file format ORM.

We can define a file format as a way of describing a binary representation of something
digital, where each subcomponent of the file format aims to represent a specific aspect
of the digital artefact, but it's not constrained to.

Two basic main operations are defined for the file format and its sub components:

 1. unpack(): the more straightforward, i.e., reading the binary data
    and build a high-level representation of that.
    Usually when unpacking you use as offset the actual offset of the
    stream and the chunk itself knows how many bytes needs to read
    to finalize the representation

 2. pack(): encode the high-level representation into binary data.

to these we add one more

 3. relayout(): trigger a recursive layout "negotiation" between a component
    and its subcomponents so to have offset and size set in the correct way.
    If not indicated explicitly a packing also implies a relayouting.

If we define a "field" as something with "direct representation" and without
subcomponents we can see that the relayouting doesn't impact on it.

An instance representing a file format can be in one of the following states

 1. INIT
 2. PACKING
 3. UNPACKING
 4. RELAYOUTING
 5. DONE
 6. ERROR

"""