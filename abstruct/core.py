import logging

from .fields import *
from .enum import Compliant
from .streams import Stream
from .exceptions import AbstructException, ChunkUnpackException
from .properties import (
    get_root_from_chunk, ChunkPhase,
)


class Meta(object):

    def __init__(self):
        self.fields = []


class MetaChunk(type):

    def __new__(cls, names, bases, attrs):
        '''All of this is a big hack, maybe too inspired by how Django does a similar thing!'''
        module = attrs.pop('__module__')
        classcell = attrs.pop('__classcell__', None)

        new_attrs = {
            '__module__': module,
        }
        if classcell is not None:
            new_attrs['__classcell__'] = classcell
        new_cls = super(MetaChunk, cls).__new__(cls, names, bases, new_attrs)

        new_cls._meta = Meta()

        # handle inheritance
        parents = [_ for _ in bases if isinstance(_, MetaChunk)]
        for parent in parents:
            for obj_name, obj in parent._meta.fields:
                new_cls.add_to_class(obj_name, obj)

        for obj_name, obj in attrs.items():
            new_cls.add_to_class(obj_name, obj)

        # create a Field to use this Chunk
        from . import fields as module_field

        real_name = '%sField' % new_cls.__name__

        cls.logger = logging.getLogger(__name__)
        cls.logger.debug('creating class \'%s\'' % real_name)

        ChunkClass = type(real_name, (Field,), {})
        ChunkClass.real = new_cls

        setattr(module_field, real_name, ChunkClass)

        return new_cls

    # TODO: factorize with Field()
    def contribute_to_chunk(self, cls, name):
        cls._meta.fields.append((name, self))

    def add_to_class(cls, name, value):
        if hasattr(value, 'contribute_to_chunk'):
            cls.logger.debug('contribute_to_chunk() found for field \'%s\'' % name)
            value.contribute_to_chunk(cls, name)
        else:
            setattr(cls, name, value)


class Chunk(metaclass=MetaChunk):
    '''
    With Field is the main class that defines a format: its main attributes
    are offset and size that identify univocally a Chunk.

    A Chunk can contain sub-chunks.

    Two main operations are defined on a Chunk:

     1. unpack(): the more straightforward, i.e., reading the binary data
        and build a high-level representation of that.
        Usually when unpacking you use as offset the actual offset of the
        stream and the chunk itself knows how many bytes needs to read
        to finalize the representation

     2. pack(): encode the high-level representation into binary data.

    All the subclasses of this generate a XField to be used as Field()
    for any Chunk the needs it.

    NOTE: you need to import fields and then call fields.XField() otherwise
    the fields won't be found.
    '''

    def __init__(self, filepath=None, father=None, offset=None, compliant=Compliant.INHERIT, **kwargs):
        self.stream = Stream(filepath) if filepath else filepath
        self.offset = offset  # can be None, an integer or a Dependency
        self.father = father
        self._phase = ChunkPhase.INIT
        self.compliant = compliant  # TODO: use an Enum to do more fine grained control over what causes exception on unpacking
        self.logger = logging.getLogger(__name__)

        for name, field_constructor in self.__class__._meta.fields:
            self.logger.debug('field \'%s\' initialized' % name)
            try:
                setattr(self, name, field_constructor(self, name=name))
            except AttributeError as e:
                raise AttributeError(f'field \'{name}\' cannot be set')

        # now we have setup all the fields necessary and we can unpack if
        # some data is passed with the constructor
        if self.stream:
            self.logger.debug('unpacking \'%s\' from %s' % (self.__class__.__name__, self.stream))
            self.unpack(self.stream)
        else:
            for name, _ in self.__class__._meta.fields:
                getattr(self, name).init()  # FIXME: understand init() logic :P

    @classmethod
    def add_dependencies(cls, father, child_name, deps):
        '''Rememebers relations between childs.
        We need to remember both r/w side.'''
        for dep in deps:
            # dependencies are indexed by the src field name
            cls._dependencies[child_name] = dep

    def get_fields(self):
        '''It returns a list of couples (name, instance) for each field.'''
        return self._meta.fields

    def __repr__(self):
        msg = []
        for field_name, _ in self.get_fields():
            field = getattr(self, field_name)
            msg.append('%s=%s' % (field_name, repr(field)))
        return '<%s(%s)>' % (self.__class__.__name__, ','.join(msg))

    def __str__(self):
        msg = ''
        for field_name, _ in self._meta.fields:
            field = getattr(self, field_name)
            msg += '%s: %s\n' % (field_name, repr(field))
        return msg

    def init(self):
        pass

    @property
    def root(self):
        '''Obtain the final father of this chunk'''
        return get_root_from_chunk(self)

    @property
    def isRoot(self):
        return self.root == self

    @property
    def phase(self):
        '''describe the status of the chunk, mainly used internally to understand
        if is ongoing packing/unpacking or whatever.

        If its children are not ongoing any process then is DONE.
        '''
        fields = [getattr(self, field_name) for field_name, _ in self._meta.fields]
        for field in fields:
            if field.phase == ChunkPhase.PROGRESS:
                return ChunkPhase.PROGRESS

        return ChunkPhase.DONE

    def size(self):
        '''the size parameter MUST not be set but MUST be derived from the subchunks'''
        size = 0
        for field_name, _ in self._meta.fields:
            field = getattr(self, field_name)
            size += field.size()

        return size

    @property
    def raw(self):
        value = b''
        for field_name, _ in self.get_fields():
            field = getattr(self, field_name)
            value += field.raw

        return value

    def relayout(self, offset=0):
        '''This method triggers the chunk's children to reset the offsets
        and the phase in order to pack correctly.

        In practice it's like packing() but it's only interested in the sizes
        of the chunks.'''
        self.offset = offset
        for field_name, _ in self.get_fields():
            self.logger.debug('relayouting %s.%s' % (self.__class__.__name__, field_name))

            field_instance = getattr(self, field_name)
            offset += field_instance.relayout(offset=offset)

        return offset

    def pack(self, stream=None, relayout=True):
        '''
        This method is a little tricky since we are creating a raw
        data encoding of the class instance.

        Should the method return the data or the stream?

        **we need to update size and offset during the packing phase**
        '''
        # if we are the root father then we can set our offset to zero
        # and initialize the stream
        if relayout:
            self.relayout()

        stream = Stream(b'') if not stream else stream

        for field_name, _ in self.get_fields():
            self.logger.debug('packing %s.%s' % (self.__class__.__name__, field_name))

            field_instance = getattr(self, field_name)

            if field_instance.offset is None:
                raise AttributeError(f'offset for field named "{field_name}" {field_instance!r} is not defined!')

            stream.seek(field_instance.offset)

            self.logger.debug('field %s set at offset %08x' % (field_name, field_instance.offset))
            # we call pack() on the subchunks
            field_instance.pack(stream=stream, relayout=False)  # we hope someone triggered the relayout before

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
        for field_name, _ in self.get_fields():
            self.logger.debug('unpacking %s.%s' % (self.__class__.__name__, field_name))
            field = getattr(self, field_name)

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
