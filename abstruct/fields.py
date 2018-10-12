import logging
import struct

from .properties import Dependency


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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
        self._references = {}
        self.father = father
        self.default = default
        self.offset = offset
        self.little_endian = little_endian
        self.formatter = formatter if formatter else '%s'

        #self.init() # FIXME: chose a convention for defining the default, maybe init_default() called from init()

    def __str__(self):
        return self.formatter % (self.value)

    def __getattribute__(self, name):
        if name != '_references' and name in self._references.keys():
            return self._references[name].get()
        return super().__getattribute__(name)

    def __setattr__(self, name, value):
        if name != '_references' and name in self._references:
            self._references[name].set(value)
        else:
            super().__setattr__(name, value)

    def configure_dependencies(self, name, ref):
        '''This tells the field that his value has some reference to external entity'''
        logger.debug('configure_dependency() for %s.%s' % (self.__class__.__name__, name))
        if name != '_references' and name in self._references:
            raise AttributeError('dependency for %s already set!' % name)

        self._references[name] = ref

    def pack(self, stream=None):
        raise NotImplemented('you need to implement this in the subclass')

    def unpack(self, stream=None):
        raise NotImplemented('you need to implement this in the subclass')


class RealStructField(RealField):
    def __init__(self, format, default=0, equals_to=None, **kw):
        super().__init__(default=default if not equals_to else equals_to, **kw)
        self.format = format

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

        super().__init__(**kw)

    def init(self):
        self.default = b'\x00' * self.n if not self.default else self.default
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

    def append(self, element):
        # TODO: check element type is correct
        self.value.append(element)
        self.n += len(self.value)

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
            logger.debug('%s: unpacking item %d' % (self.__class__.__name__, idx))
            element.unpack(stream)
            self.value.append(element)

class ArrayField(Field):
    real = RealArrayField

class RealSelectField(RealField):
    '''Associate a field with a given Chunk based on a given condition'''
    def __init__(self, fields, expression, *args, **kwargs):
        self.fields = fields
        self.expression = expression

        super().__init__(*args, **kwargs)

    def init(self):
        pass

    def unpack(self, stream):
        select = self.expression.resolve(self)

        field = self.fields[select]()

        field.unpack(stream)


class SelectField(Field):
    real = RealSelectField

class RealPaddingField(RealField):
    '''Takes as much stream as possible'''
    def unpack(self, stream):
        self.value = stream.read_all()

    def init(self):
        pass

class PaddingField(Field):
    real = RealPaddingField
