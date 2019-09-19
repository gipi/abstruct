import logging
import struct
from enum import Enum, Flag, auto

from .properties import Dependency, ChunkPhase
from .streams import Stream


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Endianess(Enum):
    LITTLE_ENDIAN = auto()
    BIG_ENDIAN    = auto()
    NETWORK       = auto()
    NATIVE        = auto()


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

    def __call__(self, father, name=None):
        if not self.real:
            raise AttributeError('property \'real\' is None')
        return self.real(*self.args, name=name, father=father, **self.kwargs)


class RealField(object):

    def __init__(self, *args, name=None, father=None, default=None, offset=None, endianess=Endianess.LITTLE_ENDIAN, little_endian=True, formatter=None, **kwargs):
        self._resolve = True  # TODO: create contextmanager
        self._phase = ChunkPhase.INIT
        self.name = name
        self.father = father
        self.default = default
        self.offset = offset
        self._value = None
        self._data = None
        self.little_endian = little_endian
        self.formatter = formatter if formatter else '%s'

        #self.init() # FIXME: chose a convention for defining the default, maybe init_default() called from init()

    def init(self):
        # here we probably need to initialize the default
        pass

    def __str__(self):
        return self.formatter % (self.value)

    def __getattribute__(self, name):
        '''If the field is a Field then return directly the 'value' attribute'''
        field = super().__getattribute__(name)
        if isinstance(field, Dependency) and self._resolve:
            logger.debug('trying to resolve dependency for \'%s\' from \'%s\'' % (name, self.name))
            return field.resolve(self)

        return field

    def __setattr__(self, name, value):
        '''This is not the opposite of __getattribute__

        For more info read the official doc <https://docs.python.org/2/reference/datamodel.html#object.__setattr__>
        '''
        self.__dict__['_resolve'] = False
        try:
            # the try block is needed in order to catch initialization of variables
            # for the first time
            field = super().__getattribute__(name)
            self.__dict__['_resolve'] = True
            if isinstance(field, Dependency):
                logger.debug('set for field \'%s\' the value \'%d\'depends on' % (name, value))
                real_field = field.resolve_field(self)
                real_field.value = value
                return
        except AttributeError:
            pass
        finally:
            self.__dict__['_resolve'] = True  # FIXME

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
        self._value = value

    def _get_value(self):
        if self._value is None:
            old_resolve = self.__dict__['_resolve']
            self.__dict__['_resolve'] = True
            self.init()
            self.__dict__['_resolve'] = old_resolve
            self._value = self.default

        return self._value

    value = property(
        fget=lambda self: self._get_value(),
        fset=lambda self, value: self._set_value(value))

    def relayout(self):
        self._resolve = False  # we don't want the automagical resolution
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

    def __init__(self, format, default=0, equals_to=None, enum=None, **kw):  # decide between default and equals_to
        self.format = format
        super().__init__(default=default if not equals_to else equals_to, **kw)

    def get_format(self):
        return '%s%s' % ('<' if self.little_endian else '>', self.format)

    def size(self):
        return struct.calcsize(self.get_format())

    @property
    def data(self):
        return self._data

    def pack(self, stream=None, relayout=True):
        self._update_value()
        packed_value = struct.pack(self.get_format(), self.value)

        stream = stream if stream else Stream(b'')

        stream.write(packed_value)

        self._phase = ChunkPhase.DONE

        return stream.getvalue()

    def unpack(self, stream):
        self._data = stream.read(self.size())
        self.value = struct.unpack(self.get_format(), self._data)[0]


class StructField(Field):
    real = RealStructField


class RealBitField(RealStructField):
    '''This class is useful when you know that the binary value in the
    field is an set of different value ORed together.
    '''
    def __init__(self, bitfield_class, format, *args, **kwargs):
        super().__init__(format, *args, **kwargs)
        self._bitfield_class = bitfield_class

    def unpack(self, stream):
        super().unpack(stream)
        self.value = self._bitfield_class(self.value)


class BitField(Field):
    real = RealBitField


# TODO: understand if it is needed to separate from Binary and alphanumeric strings.
class RealStringField(RealField):

    def __init__(self, n=0, **kw):
        super().__init__(**kw)
        self.n = n

    def init(self):
        self.default = b'\x00' * self.n if not self.default else self.default

    def _set_value(self, value):
        super()._set_value(value)
        self.n = len(self.value)

    def size(self):
        return self.n

    @property
    def data(self):
        return self.value

    def pack(self, stream=None, relayout=True):
        stream = Stream(b'') if not stream else stream

        stream.write(self.value)

        self._phase = ChunkPhase.DONE

        return stream.obj.getvalue()

    def unpack(self, stream):
        self.value = stream.read(self.n)


class StringField(Field):
    '''This in an array of "n" char'''
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

    You can indicate an explicite number of elements via the parameter named "n"
    or you can indicate with a callable returning True which element is the terminator
    for the list via the parameter named "canary".
    '''

    def __init__(self, field_cls, n=None, canary=None, **kw):
        self.field_cls = field_cls
        self.n = n
        self._canary = canary

        if n and not (isinstance(n, Dependency) or isinstance(n, int)):
            raise Exception('n is \'%s\' must be of the right type' % n.__class__.__name__)

        if 'default' not in kw:
            kw['default'] = []
            if isinstance(n, int) and n > 0:
                kw['default'] = [self.field_cls()] * self.n

        super().__init__(**kw)

    def __len__(self):
        return len(self.value)

    def count(self):
        return self.n

    @property
    def data(self):
        value = b''
        for element in self.value:
            value += element.data

        return value

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

    @property
    def phase(self):
        for field in self.value:
            if field.phase == ChunkPhase.PROGRESS:
                return ChunkPhase.PROGRESS

        return ChunkPhase.DONE

    def pack(self, stream=None, relayout=True):
        data = b''
        if relayout:
            self.relayout()

        count = 0
        while self.phase != ChunkPhase.DONE:
            for field in self.value:
                field.pack(stream=stream, relayout=False)
                field.offset = stream.tell()

            count += 1
            if count > 5:
                raise ValueError('relayouting error for class %s' % self.__class__.__name__)

        return data  # FIXME

    def unpack(self, stream):
        '''Unpack the data found in the stream creating new elements,
        the old one, if present, are discarded.'''
        self.value = []  # reset the fields already present
        real_n = self.n if self.n is not None else 100  # FIXME
        for idx in range(real_n):
            element = self.field_cls()
            logger.debug('%s: unnpacking item %d' % (self.__class__.__name__, idx))

            element_offset = stream.tell()
            element.unpack(stream)
            element.offset = element_offset

            self.value.append(element)

            if self._canary is not None:
                if self._canary(element):
                    self.n = idx
                    break


class ArrayField(Field):
    real = RealArrayField


class RealSelectField(RealField):
    '''Allow to select the kind of final field based on condition
    in the parent chunk. You need to pass the name of the field
    to use as key and a dictionary with the mapping between type
    and field. You can use Type.DEFAULT as a default.

    Like in the following example we have a format the use the first 4 bytes
    to indicate what follows: for value zero you have another 4 bytes, otherwise
    you have a ten bytes string

        class DummyType(Flag):
            FIRST = 0
            SECOND = 1

        type2field = {
            DummyType.FIRST: (fields.StructField, ('I',), {},),
            DummyType.SECOND: (fields.StringField, (0x10,), {}),
        }

        class DummyChunk(Chunk):
            type = fields.BitField(DummyType, 'I')
            data = fields.SelectField('type', type2field)
    '''
    class Type(Flag):
        DEFAULT = auto()

    def __init__(self, key, mapping, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._key = key
        self._mapping = mapping

    def init(self):
        pass

    def _get_value(self):
        return self._field.value

    @property
    def data(self):
        return self._field.data

    def unpack(self, stream):
        logger.debug('resolving key \'%s\'' % self._key)
        field_key = getattr(self.father, self._key)

        key = field_key.value if field_key.value in self._mapping else RealSelectField.Type.DEFAULT

        logger.debug('resolved key to \'%s\' (original was \'%s\')' % (key, field_key.value))

        field_class, args, kwargs = self._mapping[key]
        self._field = field_class(*args, **kwargs)
        self._field.father = self.father  # FIXME
        logger.debug('found field %s' % repr(self._field))

        self._field.unpack(stream)
        logger.debug('unpacked %s' % self._field)


class SelectField(Field):
    '''
    This field can be used like an array
    '''
    real = RealSelectField


class RealPaddingField(RealField):
    '''Takes as much stream as possible'''

    def unpack(self, stream):
        self.value = stream.read_all()

    def init(self):
        pass


class PaddingField(Field):
    real = RealPaddingField
