import logging
import struct

from .fields import *
from .streams import Stream


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Meta(object):
    def __init__(self):
        self.fields = []

class MetaChunk(type):
    def __new__(cls, names, bases , attrs):
        '''
        Uses the 'fields' attribute and attach to the new created class the relative fields.
        '''

        new_ns = {
            'field_ordering': [],
        }

        new_cls = super(MetaChunk, cls).__new__(cls, names, bases, new_ns)

        new_cls._meta = Meta()

        for obj_name, obj in attrs.items():
            new_cls.add_to_class(obj_name, obj)

        # create a Field to use this Chunk
        from . import fields as module_field

        real_name = '%sField' % new_cls.__name__

        logger.debug('creating class \'%s\'' % real_name)

        ChunkClass = type(real_name, (Field,), {})
        ChunkClass.real = new_cls

        setattr(module_field, real_name, ChunkClass)

        return new_cls

    # TODO: factorize with Field()
    def contribute_to_chunk(self, cls, name):
        cls._meta.fields.append((name, self))
        cls.set_offset(name, self.offset)

    def add_to_class(cls, name, value):
        if hasattr(value, 'contribute_to_chunk'):
            logger.debug('contribute_to_chunk() found for field \'%s\'' % name)
            cls.field_ordering.append(name)
            value.contribute_to_chunk(cls, name)
        else:
            setattr(cls, name, value)


# TODO: add compliant() to check chunk can decode (think 32 vs 64 bit ELF)
class Chunk(metaclass=MetaChunk):
    '''
    All the subclasses of this generate a XField to be used as Field()
    for any Chunk the needs it.

    NOTE: you need to import fields and then call fields.XField() otherwise
    the fields won't be found.
    '''
    _offsets = {}


    def __init__(self, filepath=None, father=None, offset=None, **kwargs):
        self.stream = Stream(filepath) if filepath else filepath
        self.offset = offset
        self.father = father

        for name, field_constructor in self.__class__._meta.fields:
            logger.debug('field \'%s\' initialized' % name)
            setattr(self, name, field_constructor(self))

        # now we have setup all the fields necessary and we can unpack if
        # some data is passed with the constructor
        if self.stream:
            self.unpack(self.stream)

    @classmethod
    def add_dependencies(cls, father, child_name, deps):
        '''Rememebers relations between childs.
        We need to remember both r/w side.'''
        for dep in deps:
            # dependencies are indexed by the src field name
            cls._dependencies[child_name] = dep

    @classmethod
    def set_offset(cls, field_name, offset):
        cls._offsets[field_name] = offset

    def __str__(self):
        msg = ''
        for field_name in self.field_ordering:
            field = getattr(self, field_name)
            msg += '%s: %s\n' % (field_name, field)
        return msg

    def resolve_offset_for_field(self, name):
        offset = self._offsets[name]

        if not offset:
            return offset

        return offset.resolve(self)

    def size(self):
        size = 0
        for field_name in self.field_ordering:
            field = getattr(self, field_name)
            size += field.size()

        return size

    def pack(self, stream=None):
        '''
        
        '''
        value = b'' if not stream else stream
        for field_name in self.field_ordering:
            value += getattr(self, field_name).pack(stream=stream)

        return value

    def unpack(self, stream):
        for field_name, _ in self._meta.fields:
            logger.debug('unpacking %s.%s' % (self.__class__.__name__, field_name))
            field = getattr(self, field_name)

            # setup the offset for this chunk
            offset = self.resolve_offset_for_field(field_name)
            if offset:
                stream.seek(offset)

            logger.debug('offset at %d' % stream.tell())

            field.unpack(stream)


