import logging
import struct

from .properties import Dependency


logger = logging.getLogger(__name__)


'''
The ratio here is that since the instances at which are attacched
the fields need to have separate instances to interact with, we need
the XFIeld() associated to the chunk to be constructor for the XChunk().
'''

class Field(object):
    real = None
    def __init__(self, *args, offset=None, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.offset = offset

    def contribute_to_chunk(self, cls, name):
        cls._meta.fields.append((name, self))
        cls.set_offset(name, self.offset)

    def __call__(self, father):
        if not self.real:
            raise AttributeError('property \'real\' is None')
        return self.real(*self.args, father=father, **self.kwargs)

class RealField(object):
    def __init__(self, *args, father=None, default=None, offset=None, little_endian=True, formatter=None, **kwargs):
        self.father = father
        self.default = default
        self.offset = offset
        self.little_endian = little_endian
        self.formatter = formatter if formatter else '%s'

        self.init()

    def __str__(self):
        return self.formatter % (self.value)

    def __getattribute__(self, name):
        '''If the field is a Field then return directly the 'value' attribute'''
        field = super().__getattribute__(name)
        if isinstance(field, Dependency):
            return field.resolve(self)

        return field

    def pack(self, stream=None):
        raise NotImplemented('you need to implement this in the subclass')

    def unpack(self, stream=None):
        raise NotImplemented('you need to implement this in the subclass')


class RealStructField(RealField):
    def __init__(self, format, default=0, **kw):
        self.format = format
        super().__init__(default=default, **kw)

    def init(self):
        self.value = self.default

    def size(self):
        return struct.calcsize(self.format)

    def pack(self, stream=None):
        return struct.pack('%s%s' % ('<' if self.little_endian else '>', self.format), self.value)

    def unpack(self, stream):
        value = stream.read(self.size())
        self.value = struct.unpack('%s%s' % ('<' if self.little_endian else '>', self.format), value)[0]


class StructField(Field):
    real = RealStructField


class RealStringField(RealField):
    def __init__(self, n, padding=0, **kw):
        self.n = n
        self.padding = padding

        if 'default' not in kw:
            kw['default'] = b'\x00'*n

        super().__init__(**kw)

    def init(self):
        padding = self.n - len(self.default)
        if padding < 0:
            raise ValueError('the default is longer than the "n" parameter')

        self.value = self.default + b'\x00'*padding

    def size(self):
        return len(self.value)

    def pack(self, stream=None):
        return self.value

    def unpack(self, stream):
        self.value = stream.read(self.n)


class StringField(Field):
    '''This in an array of "n" char with padding'''
    real = RealStringField

class StringNullTerminatedField(Field):
    def __init__(self, default='\x00', **kw):
        super().__init__(default=default, **kw)

    def init(self, default):
        self.value = default

    def pack(self, stream=None):
        return self.value

class RealArrayField(RealField):
    '''Un/Pack an array of Chunks'''
    def __init__(self, field_cls, n=0, **kw):
        self.field_cls = field_cls
        self.n = n

        if not (isinstance(n, Dependency) or isinstance(n, int)):
            raise Exception('n is \'%s\' must be of the right type' % n.__class__.__name__)

        if 'default' not in kw:
            kw['default'] = []
            if isinstance(n, int) and n > 0:
                kw['default'] = [self.field_cls()]*self.n

        super().__init__(**kw)

    def init(self):
        self.value = self.default

    def __len__(self):
        return len(self.value)

    def count(self):
        return self.n

    def size(self):
        size = 0
        for element in self.value:
            size += element.size()

        return size

    def setn(self, n):
        self.n = n

    def pack(self, stream=None):
        data = b''

        for field in self.value:
            data += field.pack()

        return data

    def unpack(self, stream):
        '''Unpack the data found in the stream creating new elements,
        the old one, if present, are discarded.'''
        self.value = [] # reset the fields already present
        for idx in range(self.n):
            element = self.field_cls()
            logger.debug('%s: unnpacking item %d' % (self.__class__.__name__, idx))
            element.unpack(stream)
            self.value.append(element)

class ArrayField(Field):
    real = RealArrayField

