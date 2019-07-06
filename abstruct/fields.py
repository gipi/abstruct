import logging
import struct

from .properties import Dependency, ChunkPhase
from .streams import Stream


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


'''
The ratio here is that since the instances at which are attacched
the fields need to have separate instances to interact with, we need
the XFIeld() associated to the chunk to be constructor for the XChunk().
'''

class Field(object):
    real = None
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def contribute_to_chunk(self, cls, name):
        cls._meta.fields.append((name, self))

    def __call__(self, father):
        if not self.real:
            raise AttributeError('property \'real\' is None')
        return self.real(*self.args, father=father, **self.kwargs)

class RealField(object):
    def __init__(self, *args, father=None, default=None, offset=None, little_endian=True, formatter=None, **kwargs):
        self._resolve = True # TODO: create contextmanager
        self._phase = ChunkPhase.INIT
        self.father = father
        self.default = default
        self.offset = offset
        self.little_endian = little_endian
        self.formatter = formatter if formatter else '%s'

        #self.init() # FIXME: chose a convention for defining the default, maybe init_default() called from init()

    def __str__(self):
        return self.formatter % (self.value)

    def __getattribute__(self, name):
        '''If the field is a Field then return directly the 'value' attribute'''
        field = super().__getattribute__(name)
        if isinstance(field, Dependency) and name != 'default' and self._resolve: # FIXME: epic workaround
            logger.debug('trying to resolve dependency for \'%s\'' % name)
            return field.resolve(self)

        return field

    def __setattr__(self, name, value):
        '''This is not the opposite of __getattribute__

        For more info read the official doc <https://docs.python.org/2/reference/datamodel.html#object.__setattr__>
        '''
        try:
            # the try block is needed in order to catch initialization of variables
            # for the first time
            self.__dict__['_resolve'] = False
            field = super().__getattribute__(name)
            self.__dict__['_resolve'] = True
            if isinstance(field, Dependency) and name != 'default': # FIXME: epic workaround
                logger.debug('set for field \'%s\' the value \'%d\'depends on' % (name, value))
                real_field = field.resolve_field(self)
                real_field.value = value
                return
        except AttributeError:
            pass
        finally:
            self.__dict__['_resolve'] = True # FIXME

        super().__setattr__(name, value)

    @property
    def phase(self):
        return self._phase

    def __set_offset(self, value):
        self.__offset = value

    def __get_offset(self):
        return self.__offset

    offset = property(__get_offset, __set_offset)

    def _set_value(self, value):
        self.__value = value

    def _get_value(self):
        return self.__value

    value = property(
        fget=lambda self: self._get_value(),
        fset=lambda self, value: self._set_value(value))

    def relayout(self):
        self._resolve = False # we don't want the automagical resolution
        if not isinstance(self.offset, Dependency):
            self.offset = None
            self._phase = ChunkPhase.PROGRESS

        self._resolve = True

    def _update_value(self):
        '''This is used to update the binary value before packing'''
        pass

    def pack(self, stream=None, relayout=True):
        '''The pack-ing action needs to take into consideration the fact that we need
        to eventually update fields that depends on other fields

        This operation is not idempotent!
        '''
        raise NotImplemented('you need to implement this in the subclass')

    def unpack(self, stream=None):
        raise NotImplemented('you need to implement this in the subclass')


class RealStructField(RealField):
    def __init__(self, format, default=0, equals_to=None, **kw):
        self.format = format
        super().__init__(default=default if not equals_to else equals_to, **kw)

    def init(self):
        self.value = self.default

    def size(self):
        return struct.calcsize(self.format)

    def pack(self, stream=None, relayout=True):
        self._update_value()
        packed_value = struct.pack('%s%s' % ('<' if self.little_endian else '>', self.format), self.value)

        stream = stream if stream else Stream(b'')

        stream.write(packed_value)

        return stream.getvalue()

    def unpack(self, stream):
        value = stream.read(self.size())
        self.value = struct.unpack('%s%s' % ('<' if self.little_endian else '>', self.format), value)[0]


class StructField(Field):
    real = RealStructField


'''
TODO: understand if it is needed to separate from Binary and alphanumeric strings.
'''
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

    def _set_value(self, value):
        super()._set_value(value)
        self.n = len(self.value)

    def size(self):
        return len(self.value)

    def pack(self, stream=None, relayout=True):
        stream = Stream(b'') if not stream else stream

        stream.write(self.value)

        return stream.obj.getvalue()

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

    def pack(self, stream=None, relayout=True):
        return self.value

class RealArrayField(RealField):
    '''Un/Pack an array of Chunks.

    TODO: add a parameter to choose when the array must stop, like a particular data value.
    '''
    def __init__(self, field_cls, n=None, **kw):
        self.field_cls = field_cls
        self.n = n

        if n and not (isinstance(n, Dependency) or isinstance(n, int)):
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

    def relayout(self):
        super().relayout()
        for field in self.value:
            field.relayout()

    def pack(self, stream=None, relayout=True):
        data = b''
        if relayout:
            self.relayout()

        for field in self.value:
            field.pack(stream=stream, relayout=False)
            field.offset = stream.tell()

        return data # FIXME

    def unpack(self, stream):
        '''Unpack the data found in the stream creating new elements,
        the old one, if present, are discarded.'''
        self.value = [] # reset the fields already present
        real_n = self.n if self.n is not None else 100 # FIXME
        for idx in range(real_n):
            element = self.field_cls()
            logger.debug('%s: unnpacking item %d' % (self.__class__.__name__, idx))
            try:
                element_offset = stream.tell()
                element.unpack(stream)
                element.offset = element_offset

                self.value.append(element)
            except:
                self.n = idx
                break

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
