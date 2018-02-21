import struct

from .properties import Dependencies


class MetaField(type):
    def __init__(cls, names, bases, ns):
        mandatory_methods = [
            'init', # FIXME: maybe use only "default" __init__ param
            'pack',
        ]
        for method in mandatory_methods:
            if method not in ns.keys() and names != 'Field':
                raise ValueError('you must implement %s() method for the class \'%s\'' % (method, names))

class Field(metaclass=MetaField):
    def __init__(self, name=None, little_endian=True, default=None, offset=None):
        self.name = name
        self.little_endian = little_endian
        self.offset = offset

        self.init(default=default)

    def contribute_to_chunk(self, cls, name):
        setattr(cls, name, self)
        cls.set_offset(name, self.offset)

    def pack(self, stream=None):
        raise NotImplemented('you need to implement this in the subclass')

    def __str__(self):
        return '%s' % (self.value)


class StructField(Field):
    def __init__(self, format, default=0, **kw):
        self.format = format
        super(StructField, self).__init__(default=default, **kw)

    def init(self, default):
        self.value = default

    def size(self):
        return struct.calcsize(self.format)

    def pack(self, stream=None):
        return struct.pack('%s%s' % ('<' if self.little_endian else '>', self.format), self.value)

    def unpack(self, stream):
        value = stream.read(self.size())
        self.value = struct.unpack('%s%s' % ('<' if self.little_endian else '>', self.format), value)[0]


class StringField(Field):
    '''This in an array of "n" char with padding'''
    def __init__(self, n, padding=0, **kw):
        self.n = n
        self.padding = padding

        if 'default' not in kw:
            kw['default'] = b'\x00'*n

        super(StringField, self).__init__(**kw)

    def init(self, default):
        padding = self.n - len(default)
        if padding < 0:
            raise ValueError('the default is longer than the "n" parameter')

        default = default + b'\x00'*padding

        self.value = default

    def size(self):
        return len(self.value)

    def pack(self, stream=None):
        return self.value

    def unpack(self, stream):
        self.value = stream.read(self.n)


class StringNullTerminatedField(Field):
    def __init__(self, default='\x00', **kw):
        super(StringField, self).__init__(default=default, **kw)

    def init(self, default):
        self.value = default

    def pack(self, stream=None):
        return self.value

class ArrayField(Field):
    '''Un/Pack an array of Chunks'''
    def __init__(self, field_cls, n=0, **kw):
        self.field_cls = field_cls

        if isinstance(n, str):
            n = Dependencies(n)

        if isinstance(n, Dependencies):
            self.n = n
            #self.dependencies.append(self.n)
        elif isinstance(n, int):
            self.n = n
        else:
            raise Exception('n must be of the right type')


        if 'default' not in kw:
            kw['default'] = []
            if isinstance(n, int) and n > 0:
                kw['default'] = [self.field_cls()]*self.n

        super(ArrayField, self).__init__(**kw)

    def init(self, default):
        self.value = default

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
        index = 0

        for element in self.value:
            logger.debug('%s: unnpacking item %d' % (self.__class__.__name__, index))
            element.unpack(stream[index:])
            index += element.size()

