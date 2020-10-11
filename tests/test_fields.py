from enum import Enum, auto

import pytest

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
