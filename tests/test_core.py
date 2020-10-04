from enum import Enum, auto

import pytest

from abstruct.core import Chunk
from abstruct.enum import Compliant
from abstruct.exceptions import UnpackException
from abstruct.fields import StructField, StringField


def test_structfield_conversion_raw_value():
    """Check that the attributes "value" and "raw" are the analogous
    of the integers and bytes representation for a field.

    NOTE: this should be done for all the fields."""
    field = StructField('I')

    assert field.size == 4
    assert field.raw == b'\x00\x00\x00\x00'
    assert field.value == 0

    field.value = 0xcafe

    assert field.value == 0xcafe
    assert field.raw == b'\xfe\xca\x00\x00'


def test_structfield_set_raw():
    field = StructField('I')

    field.raw = b'\x01\x02\x03\x04'
    assert field.value == 0x04030201


def test_structfield_enum():
    class DummyEnum(Enum):
        NONE = 0
        FIRST = auto()
        SECOND = auto()

    field = StructField('I', enum=DummyEnum, compliant=Compliant.ENUM)

    assert field.value == DummyEnum.NONE

    field.value = DummyEnum.SECOND

    assert field.value == DummyEnum.SECOND
    assert field.raw == b'\x02\x00\x00\x00'

    with pytest.raises(UnpackException):
        field.raw = b'\x04\x00\x00\x00'


def test_stringfield():
    field = StringField(0x10)

    assert field.size == 0x10
    assert len(field.raw) == field.size
    assert field.raw == b'\x00' * field.size

    with pytest.raises(ValueError):
        field.value = b'kebab'

    data = b''.join([bytes([_]) for _ in range(0x10)])

    field.value = data

    assert field.value == data
    assert field.raw == data


def test_chunk():
    """Check that building a Chunk from fields behaves correctly."""
    class Dummy(Chunk):
        a = StructField('I', default=0xbad)
        b = StringField(0x10)
        c = StructField('I', default=0xdeadbeef)

    dummy = Dummy()

    assert dummy.a.size == 4
    assert dummy.a.raw == b'\xad\x0b\x00\x00'
    assert dummy.a.value == 0xbad
    assert dummy.a.offset == 0x00

    assert dummy.b.size == 0x10
    assert dummy.b.raw == b'\x00' * 0x10
    assert dummy.b.offset == 0x04

    assert dummy.c.size == 0x4
    assert dummy.c.raw == b'\xef\xbe\xad\xde'
    assert dummy.c.offset == 0x14

    assert dummy.size == 0x18
    assert len(dummy.raw) == dummy.size
    assert dummy.raw == (
        b'\xad\x0b\x00\x00' +
        b'\x00' * 0x10 +
        b'\xef\xbe\xad\xde'
    )


def test_proxy_like_format():
    """Check that a file format having sub-components referring to overlapping data
    behaves gently.

    Some formats (ELF *cough*) have different sub-components that refer to the same underlying
    data, often with different representation of it.
    """

    class Proxy(Chunk):
        off = StructField('I')
        sz = StructField('I')

    class Experiment(Chunk):
        """
        Simple file format where two header-like fields intercept overlapping data into the file.
        """
        proxy_a = Proxy()
        proxy_b = Proxy()

        contents = StringField(0x100)

    experiment = Experiment()

    assert experiment.layout == {
        'proxy_a': (0, 8),
        'proxy_b': (8, 8),
        'contents': (16, 256),
    }

    assert experiment.size == 0x100 + 2 * (4 + 4)
    assert len(experiment.raw) == experiment.size
    assert experiment.raw == b'\x00' * experiment.size
