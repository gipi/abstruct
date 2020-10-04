"""
Core module for the abstraction of a file format

"""
import logging
from typing import Tuple, List, Dict

from .fields import Field
from .enum import Compliant
from .meta import MetaChunk
from .streams import Stream
from .exceptions import (
    ChunkUnpackException,
    UnpackException,
    MagicException,
)
from .properties import (
    get_root_from_chunk,
    Dependency,
    ChunkPhase,
)


class Chunk(Field, metaclass=MetaChunk):
    """
    Together with Field is the main class that defines a format: its main attributes
    are offset and size that identify a Chunk.

    A Chunk can contain sub-chunks.

    All the subclasses of this generate a XField to be used as Field()
    for any Chunk the needs it.

    NOTE: you need to import fields and then call fields.XField() otherwise
    the fields won't be found.
    """

    def __init__(self, filepath=None, **kwargs):
        self.stream = Stream(filepath) if filepath is not None else filepath
        super().__init__(**kwargs)

        # now we have setup all the fields necessary and we can unpack if
        # some data is passed with the constructor
        if self.stream:
            self.logger.debug('unpacking \'%s\' from %s' % (self.__class__.__name__, self.stream))
            self.unpack(self.stream)
        else:
            # for name in self.__class__._meta.fields:
            #    getattr(self, name).init()  # FIXME: understand init() logic :P

            self.relayout()

    def get_ordered_fields_name(self) -> List[str]:
        return self._meta.fields

    def get_fields(self) -> List[Tuple[str, Field]]:
        '''It returns a list of couples (name, instance) for each field.'''
        return [(_, getattr(self, _)) for _ in self.get_ordered_fields_name()]

    def get_dependencies(self) -> Dict[str, Dependency]:
        dep = super().get_dependencies()

        for field_name, field in self.get_fields():
            for key, value in field.get_dependencies().items():
                dep.update({f'{field_name}.{key}': value})

        return dep

    def get_reverse_dependencies(self) -> Dict[str, str]:
        """This builds the ADG of the dependencies under the point of view of the packing."""
        deps = self.get_dependencies()

        reverse_deps: Dict[str, str] = {}

        def _first_not_empty(_seq):
            _iter = iter(_seq)
            while (element := next(_iter)) == '':
                pass

            return element

        # we are going to loop over the dependencies
        for reference, dep in deps.items():
            # to find the outermost elements
            field_dst_name = _first_not_empty(reference.split("."))
            field_src_name = _first_not_empty(dep.expression.split("."))

            # check it's resolved internally by the field itself
            if field_dst_name == field_src_name:
                continue

            reverse_deps[field_src_name] = field_dst_name

        return reverse_deps

    def __repr__(self):
        msg = []
        for field_name, field in self.get_fields():
            msg.append('%s=%s' % (field_name, repr(field)))
        return '<%s(%s)>' % (self.__class__.__name__, ','.join(msg))

    def __str__(self):
        msg = ''
        for field_name in self._meta.fields:
            field = getattr(self, field_name)
            msg += '%s: %s\n' % (field_name, repr(field))
        return msg

    def init(self):
        for _, field in self.get_fields():
            field.init()

    @property
    def root(self):
        '''Obtain the final father of this chunk'''
        return get_root_from_chunk(self)

    @property
    def isRoot(self):
        return self.root == self

    def _get_size(self):
        '''the size parameter MUST not be set but MUST be derived from the subchunks'''
        size = 0
        for field_name in self._meta.fields:
            field = getattr(self, field_name)
            size += field.size

        return size

    @property
    def raw(self):
        value = b''
        for field_name, field_instance in self.get_fields():
            field_raw = field_instance.raw
            self.logger.debug("field '{}' raw={}".format(field_name, field_raw))
            value += field_raw


        return value

    @property
    def layout(self) -> Dict[str, Tuple[int, int]]:
        result = {}
        for name, field in self.get_fields():
            result[name] = (field.offset, field.size)

        return result

    def relayout(self, offset=0):
        '''This method triggers the chunk's children to reset the offsets
        and the phase in order to pack correctly.

        In practice it's like packing() but it's only interested in the sizes
        of the chunks.'''
        phase_old = self._phase
        self._phase = ChunkPhase.RELAYOUTING
        self.offset = offset

        size = 0
        for field_name, field_instance in self.get_fields():
            self.logger.debug('relayouting %s.%s' % (self.__class__.__name__, field_name))
            size += field_instance.relayout(offset=offset + size)

        self._phase = phase_old

        return size

    def pack(self, stream=None, relayout=True):
        '''
        This method is a little tricky since we are creating a raw
        data encoding of the class instance.

        Should the method return the data or the stream?

        **we need to update size and offset during the packing phase**
        '''
        self._phase = ChunkPhase.PACKING
        # if we are the root father then we can set our offset to zero
        # and initialize the stream
        if relayout:
            self.relayout()

        stream = Stream(b'') if not stream else stream

        for field_name, field_instance in self.get_fields():
            self.logger.debug('packing %s.%s' % (self.__class__.__name__, field_name))


            if field_instance.offset is None:
                raise AttributeError(f'offset for field named "{field_name}" {field_instance!r} is not defined!')

            stream.seek(field_instance.offset)

            self.logger.debug('field %s set at offset %08x' % (field_name, field_instance.offset))
            # we call pack() on the subchunks
            field_instance.pack(stream=stream, relayout=False)  # we hope someone triggered the relayout before

        self._phase = ChunkPhase.PACKING

        return stream.obj.getvalue()

    def unpack(self, stream):
        '''This is one of the main APIs to take care of: its aim is to take a binary
        data and transform in the representation given by the class this method
        is implemented.

        Passing a stream is mandatory since is possible that the different
        sub-chunks can have offsets not contiguous so we need to jump back and
        forth.

        As already told size and offset are the two fundamental parameters that
        define a chunk inside a binary stream:

        There are some aspects that have to take in consideration:

            1. you can have size and offset dependencies
            2. you can enforce dependencies or not
        '''
        self._phase = ChunkPhase.UNPACKING
        for field_name, field in self.get_fields():
            self.logger.debug('unpacking %s.%s' % (self.__class__.__name__, field_name))

            # setup the offset for this chunk
            offset = field.offset
            if offset:
                stream.seek(offset)
            else:
                offset = stream.tell()

            self.logger.debug('offset at %d' % stream.tell())

            try:
                field.unpack(stream)
            except (UnpackException, ChunkUnpackException) as e:
                chain = e.chain if isinstance(e, ChunkUnpackException) else []
                chain.append(field_name)
                raise ChunkUnpackException(chain=chain)
            field.offset = offset

        if hasattr(self, 'validate'):
            ret = self.validate()
            if not ret:
                self.logger.warning(f'magic for field \'{self.name}\' failed')
                if self.compliant & Compliant.MAGIC:
                    raise MagicException(chain=[])
