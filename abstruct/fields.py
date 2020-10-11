"""
A Field is "fundamental" datatype from the format point of view, something directly
packable/unpackable without need for relayouting.
"""
import logging
import struct
import copy
from enum import Enum, Flag, auto
from functools import lru_cache
from typing import Dict

from .enum import Compliant
from .meta import FieldBase, Endianess
from .properties import Dependency, ChunkPhase, PropertyDescriptor
from .streams import Stream, Backend
from .exceptions import UnpackException, MagicException


class Field(FieldBase):
    """Base class to subclass from"""

    def __init__(self, *args, name=None, father=None, default=None, offset=None, size=None, \
                 endianess=Endianess.LITTLE_ENDIAN, compliant=Compliant.INHERIT, is_magic=False):
        super().__init__()
        self._phase = ChunkPhase.INIT
        self.logger = logging.getLogger(__name__)
        self._dependencies: Dict[str, Dependency] = {}
        self._resolve = True  # TODO: create contextmanager
        self.name = name
        self.father = father
        self.default = default
        self.offset = offset
        self._size = size
        self._backend = Backend()
        self.endianess = endianess
        self.compliant = compliant
        self.is_magic = is_magic

        self.init()  # FIXME: chose a convention for defining the default, maybe init_default() called from init()

    def init(self):
        # here we probably need to initialize the default
        self.value = self.value_from_default()

    def value_from_default(self):
        return self.default

    def __str__(self):
        return str(self.value)

    def get_backend(self):
        """This is the backend used by the field for storage operations."""
        if self.father:
            return self.father.get_backend()

        return self._backend

    def get_dependencies(self):
        """Return the dictionary containing as key the field"""
        instance_dict = self.__dict__
        return {_k: _v for _k, _v in instance_dict.items() if isinstance(_v, Dependency)}

    def is_compliant(self, level):
        '''Returns the compliant'''
        instance = self
        while instance:
            if instance.compliant & level:
                return True
            if not instance.compliant & Compliant.INHERIT:
                break

            instance = instance.father

        return False

    def __set_offset(self, value):
        self.__offset = value

    def __get_offset(self):
        return self.__offset

    offset = property(__get_offset, __set_offset)

    value = property(
        fget=lambda self: self._get_value(),
        fset=lambda self, value: self._set_value(value))

    def _get_size(self):
        raise NotImplementedError(f"method {self.__class__.__name__}_get_size() not implemented")

    size = property(
        fget=lambda self: self._get_size(),
    )

    def _get_raw(self) -> bytes:
        raise NotImplementedError()

    def _set_raw(self, value) -> None:
        raise NotImplementedError(f"method {self.__class__.__name__}._set_raw() not implemented")

    raw = property(
        fget=lambda self: self._get_raw(),
        fset=lambda self, value: self._set_raw(value),
    )

    def relayout(self, offset=0, reset=False):
        self.logger.debug("relayouting %s", self.__class__)
        old_phase = self._phase
        self._phase = ChunkPhase.RELAYOUTING
        self.offset = offset

        if reset:
            self.init()

        self._phase = old_phase

        return self.size

    def _update_value(self):
        '''This is used to update the binary value before packing'''
        pass

    def pack(self, stream=None, relayout=True):
        '''The pack-ing action needs to take into consideration the fact that we need
        to eventually update fields that depends on other fields

        This operation is not idempotent!
        '''
        raise NotImplemented('you need to implement this in the subclass')

    def unpack(self, stream):
        raise NotImplemented('you need to implement this in the subclass')


class StructField(Field):
    """
    Simplest of the fields: mimic the behaviour of the struct module packing/unpacking
    integers to/from bytes.

    The main advantage is the possibility to indicate via the "enum" argument some subclass
    of enum.Enum so to have directly a representation of the integer value of the field itself.
    """

    # FIXME: make the enum internal mechanism overridable so to have arch-dependent-enums
    def __init__(self, format, default=0, equals_to=None, enum=None, **kw):  # decide between default and equals_to
        self.format = format
        self.enum = enum
        super().__init__(default=default if not equals_to else equals_to, **kw)

    def _get_encoder(self):
        return str if isinstance(self.value, bytes) else hex

    def __repr__(self):
        if not self.enum:
            return '<%s(%s)>' % (self.__class__.__name__, self._get_encoder()(self.value))

        return f'<{self.__class__.__name__}({self.value!r})>'

    def __str__(self):
        if self.format == 'c':
            return self.value.decode('latin1')
        width = self.size() * 2  # we want to be as large as possible
        formatter = '0x%%0%dx' % width
        return formatter % (self.value if not self.enum else self.value.value,)

    def value_from_default(self):
        if not self.enum:
            return super().value_from_default()

        return self.enum(self.default)

    def get_format(self):
        return '%s%s' % ('<' if self.endianess == Endianess.LITTLE_ENDIAN else '>', self.format)

    @lru_cache
    def _get_value(self):
        raw = self.get_backend().\
            seek(self.offset if self.offset is not None else 0).\
            read(self.size)
        return self._unpack(raw)

    def _set_value(self, value) -> None:
        raw = struct.pack(self.get_format(), value if not self.enum else value.value)
        # TODO: factorize
        self.get_backend().seek(self.offset if self.offset is not None else 0)
        self.get_backend().write(raw)
        self._get_value.cache_clear()

    def _get_size(self):
        return struct.calcsize(self.get_format())

    def _get_raw(self) -> bytes:  # TODO: factorize
        self.get_backend().seek(self.offset if self.offset is not None else 0)
        return self.get_backend().read(self.size)

    def _set_raw(self, raw: bytes) -> None:
        self.get_backend()\
            .seek(self.offset if self.offset is not None else 0)\
            .write(raw)
        self._get_value.cache_clear()
        value = self.value

    def _unpack_struct(self, value: bytes) -> int:
        try:
            unpacked_value = struct.unpack(self.get_format(), value)[0]
        except struct.error as e:
            self.logger.error(e)
            exc = MagicException if self.is_compliant(Compliant.MAGIC) else UnpackException
            raise exc(chain=[])

        return unpacked_value

    def _unpack_enum(self, value: int) -> Enum:
        try:
            return self.enum(value)
        except ValueError as e:
            instance = self
            while instance:
                if instance.compliant & Compliant.ENUM:
                    raise UnpackException(chain=[])
                if not instance.compliant & Compliant.INHERIT:
                    break

                instance = instance.father

            self.logger.warning(f'enum {self.enum!r} doesn\'t have element with value 0x{value:x} in it')

    def _unpack(self, raw):
        value = self._unpack_struct(raw)
        if self.enum:
            value = self._unpack_enum(value)

        if self.is_magic and value != self.default:
            self.logger.warning(f'the magic doesn\'t correspond')
            if self.is_compliant(Compliant.MAGIC):
                raise MagicException(chain=[])

        return value

# TODO: understand if it is needed to separate from Binary and alphanumeric strings.
class StringField(Field):
    """Represent a contiguous chunk of bytes."""

    length = PropertyDescriptor('length', int)

    def __init__(self, n=None, **kw):
        if n is None and 'default' not in kw:
            raise ValueError(f"StringField must have 'n' or 'default' indicated!")

        self.length = n or len(kw['default'])

        super().__init__(**kw)

    def __repr__(self):
        return '<%s(%s)>' % (self.__class__.__name__, repr(self.value))

    def __len__(self):
        return self.length

    def value_from_default(self):
        return b'\x00' * self.length if not self.default else self.default

    def _get_size(self):
        return self.length

    @lru_cache
    def _get_value(self):
        raw = self.get_backend().\
            seek(self.offset if self.offset is not None else 0).\
            read(self.size)
        return raw

    def _set_value(self, value) -> None:
        """The StringField has the size as a parameter and we must follow that indication
        unless it's a Dependency, in that case we are going to write back the value where necessary."""
        length = len(value)
        if 'length' not in self.get_dependencies() and length != self.length:
            raise ValueError(f'you are trying to set a value with the wrong size (that is {self.length} bytes)')

        raw = value  # TODO: factorize
        self.get_backend().seek(self.offset if self.offset is not None else 0)
        self.get_backend().write(raw)

        # TODO: do this only on Dependency?
        self.length = length

        self._get_value.cache_clear()
        value = self.value

    def _get_raw(self):
        return self.value


class FixedLengthString(StringField):
    """This field can contain only binary strings with fixed length."""
    def __init__(self, length):
        super().__init__(n=length)

    def _set_value(self, value) -> None:
        if len(value) != self.length:
            raise ValueError(f"class '{self.__class__.__name__}' can only accept binary strings of length {self.length}")

        super()._set_value(value)


class ArrayField(Field):
    '''Un/Pack an array of Chunks.

    You can indicate an explicite number of elements via the parameter named "n"
    or you can indicate with a callable returning True which element is the terminator
    for the list via the parameter named "canary".

    This class must behave like a list in python, obviously cannot implement all the methods
    since, for example, slicing what should mean?
    '''

    def __init__(self, field_cls, n=0, canary=None, **kw):
        self.field_cls = field_cls
        if n and not (isinstance(n, Dependency) or isinstance(n, int)):
            raise Exception('n is \'%s\' must be of the right type' % n.__class__.__name__)

        if 'default' not in kw:
            kw['default'] = []
            if isinstance(n, int) and n > 0:
                kw['default'] = [self.instance_element()] * n

        super().__init__(**kw)
        self._n = n
        self._canary = canary

    def __repr__(self):
        return f'<{self.__class__.__name__}({self.value!r})>'

    def __getitem__(self, item):
        return self.value[item]

    def __len__(self):
        return len(self.value)

    def _set_value(self, value):
        super()._set_value(value)
        self._n = len(self.value)

    def clear(self):
        self.value.clear()

    @property
    def raw(self):
        value = b''
        for element in self.value:
            value += element.raw

        return value

    def _get_size(self):
        size = 0
        for element in self.value:
            size += element.size

        return size

    def relayout(self, offset=0):
        super().relayout(offset=offset)
        size = 0
        for field in self.value:
            size += field.relayout(offset=offset + size)

        return size


            self.__class__.__name__,
            self.name,
        ))

    def instance_element(self):
        return self.field_cls.create(father=self)  # pass the father so that we don't lose the hierarchy

    def unpack_element(self, element, stream):
        element.unpack(stream)

    def append(self, element):
        element.father = self
        self.value.append(element)
        self._n = len(self.value)



class SelectField(Field):
    """Allow to select the kind of final field based on condition in the parent chunk.
    You need to pass the name of the field to use as key and a dictionary with the mapping
    between type and field. You can use Type.DEFAULT as a default.

    Like in the following example we have a format the use the first 4 bytes to indicate what
    follows: for value zero you have another 4 bytes, otherwise you have a ten bytes string

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
    """
    class Type(Flag):
        DEFAULT = auto()

    def __init__(self, key, mapping, *args, **kwargs):
        self._key = key
        self._mapping = mapping
        self._field = None

        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f'<{self.__class__.__name__}{self._field!r}>'

    def value_from_default(self):
        key = self.default if self.default in self._mapping else SelectField.Type.DEFAULT
        self._field = self._mapping[key]

        return self._field.value_from_default()

    def _get_value(self):
        return self._field.value

    def _set_value(self, value):
        self._field.value = value

    @property
    def raw(self) -> bytes:
        return self._field.raw

    def _get_size(self) -> int:
        return self._field.size

    def unpack(self, stream):
        self.logger.debug('resolving key \'%s\'' % self._key)
        field_key = getattr(self.father, self._key)

        key = field_key.value if field_key.value in self._mapping else SelectField.Type.DEFAULT

        self.logger.debug('using key to \'%s\' (original was \'%s\')' % (key, field_key.value))

        field_class, args, kwargs = self._mapping[key]
        self._field = field_class(*args, **kwargs)
        self._field.father = self.father  # FIXME
        self.logger.debug(f'unpacking {self._field!r}')

        self._field.unpack(stream)
        self.logger.debug(f'unpacked {self._field!r}')


class PaddingField(Field):
    '''Takes as much stream as possible'''

    def unpack(self, stream):
        self.value = stream.read_all()

    def init(self):
        pass
