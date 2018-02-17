import struct

class MetaField(type):
    def __init__(cls, names, bases, ns):
        mandatory_methods = [
            'init', # FIXME: maybe use only "default" __init__ param
            'pack',
        ]
        for method in mandatory_methods:
            if method not in ns.keys() and names != 'Field':
                raise ValueError('you must implement %s() method for the class \'%s\'' % (method, names))

class Field(object):
    __metaclass__ = MetaField
    def __init__(self, name=None, little_endian=True, default=None):
        self.name = name
        self.little_endian = little_endian

        self.init(default=default)

    def pack(self):
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
        return len(self.pack())

    def pack(self):
        return struct.pack('%s%s' % ('<' if self.little_endian else '>', self.format), self.value)

    def unpack(self, value):
        self.value = struct.unpack('%s%s' % ('<' if self.little_endian else '>', self.format), value)[0]


class StringField(Field):
    '''This in an array of "n" char with padding'''
    def __init__(self, n, padding=0, **kw):
        self.n = n
        self.padding = padding

        if not kw.has_key('default'):
            kw['default'] = '\x00'*n

        super(StringField, self).__init__(**kw)

    def init(self, default):
        padding = self.n - len(default)
        if padding < 0:
            raise ValueError('the default is longer than the "n" parameter')

        default = default + '\x00'*padding

        self.value = default

    def size(self):
        return len(self.value)

    def pack(self):
        return self.value

    def unpack(self, value):
        self.value = value


class StringNullTerminatedField(Field):
    def __init__(self, default='\x00', **kw):
        super(StringField, self).__init__(default=default, **kw)

    def init(self, default):
        self.value = default

    def pack(self):
        return self.value


class MetaChunk(type):
    def __new__(cls, names, bases , ns):
        '''
        Uses the 'fields' attribute and attach to the new created class the relative fields.
        '''

        new_ns = {
            'field_ordering': [],
        }

        # FIXME: maybe is better to pop 'fields'
        for key, value in ns.iteritems():
            if key != 'fields':
                new_ns[key] = value
            else:
                for name, field in value:
                    new_ns[name] = field if not isinstance(field, str) else StructField(field)# add an attribute to the class
                    new_ns['field_ordering'].append(name) # remember the order of the field

        return super(MetaChunk, cls).__new__(cls, names, bases, new_ns)

    def __init__(cls, names, bases, namespaces):
        pass


class Chunk(object):
    __metaclass__ = MetaChunk

    def __init__(self):
        pass

    def __str__(self):
        msg = ''
        for field_name in self.field_ordering:
            field = getattr(self, field_name)
            msg += '%s: %s\n' % (field_name, field)
        return msg

    def pack(self):
        value = ''
        for field_name in self.field_ordering:
            value += getattr(self, field_name).pack()

        return value

    def unpack(self, data):
        index = 0
        for field_name in self.field_ordering:
            field = getattr(self, field_name)
            size = field.size()

            field.unpack(data[index:index+size])

            index += size

class ArrayField(Field):
    '''Un/Pack an array of adjacent Chunk'''
    def __init__(self, field_cls, n=0, **kw):
        self.n = n
        self.field_cls = field_cls

        if not kw.has_key('default'):
            if n > 0:
                kw['default'] = [self.field_cls()]*self.n
            else:
                kw['default'] = []

        super(ArrayField, self).__init__(**kw)

    def init(self, default):
        self.value = default

    def count(self):
        return len(self.value)

    def pack(self):
        data = ''

        for field in self.value:
            data += field.pack()

        return data



