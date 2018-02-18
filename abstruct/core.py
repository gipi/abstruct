import struct
from .fields import *



class MetaChunk(type):
    def __new__(cls, names, bases , attrs):
        '''
        Uses the 'fields' attribute and attach to the new created class the relative fields.
        '''

        new_ns = {
            'field_ordering': [],
        }

        new_cls = super(MetaChunk, cls).__new__(cls, names, bases, new_ns)

        for obj_name, obj in attrs.items():
            new_cls.add_to_class(obj_name, obj)

        return new_cls

    def add_to_class(cls, name, value):
        if hasattr(value, 'contribute_to_chunk'):
            cls.field_ordering.append(name)
            value.contribute_to_chunk(cls, name)
        else:
            setattr(cls, name, value)

    def __init__(cls, names, bases, namespaces):
        pass


# TODO: add compliant() to check chunk can decode (think 32 vs 64 bit ELF)
class Chunk(metaclass=MetaChunk):

    def contribute_to_chunk(self, cls, name):
        setattr(cls, name, self)

    def __init__(self):
        self._dependencies = {}

    def add_relation(self, a, b):
        '''Rememebers relations between childs'''

    def __str__(self):
        msg = ''
        for field_name in self.field_ordering:
            field = getattr(self, field_name)
            msg += '%s: %s\n' % (field_name, field)
        return msg

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
        index = 0

        data = stream # FIXME

        for field_name in self.field_ordering:
            field = getattr(self, field_name)
            size = field.size()

            field.unpack(data[index:index + size])

            index += size

