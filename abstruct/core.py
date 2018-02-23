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

        RealChunkClass = type(real_name, (object,), {})
        RealChunkClass.real = new_cls

        setattr(module_field, real_name, RealChunkClass)
        return new_cls

    def add_to_class(cls, name, value):
        if hasattr(value, 'contribute_to_chunk'):
            cls.field_ordering.append(name)
            value.contribute_to_chunk(cls, name)
        else:
            setattr(cls, name, value)


# TODO: add compliant() to check chunk can decode (think 32 vs 64 bit ELF)
class Chunk(metaclass=MetaChunk):
    _dependencies = {}
    _offsets = {}

    # TODO: factorize with Field()
    def contribute_to_chunk(self, cls, name):
        cls.set_offset(name, self.offset)

    def __init__(self, filepath=None, offset=None):
        self.stream = Stream(filepath) if filepath else filepath
        self.offset = offset

        if self.stream:
            self.unpack(self.stream)

        for name, field_constructor in self.__class__._meta.fields:
            logger.debug('field \'%s\' initialized' % name)
            setattr(self, name, field_constructor(self))

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
        for field_name in self.field_ordering:
            logger.debug('unpacking %s.%s' % (self.__class__.__name__, field_name))
            field = getattr(self, field_name)

            # setup the offset for this chunk
            offset = self.resolve_offset_for_field(field_name)
            if offset:
                stream.seek(offset)

            field.unpack(stream)


