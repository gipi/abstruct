from enum import Enum, auto, Flag

import pytest

from abstruct.enum import Compliant
from abstruct.exceptions import UnpackException
from abstruct.fields import StructField, StringField, SelectField, ArrayField


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


def test_selectfield():
    class DummyType(Flag):
        FIRST = 0
        SECOND = 1

    type2field = {
        DummyType.FIRST: StructField('I', default=0xcafebabe),
        DummyType.SECOND: StringField(0x10, default=b'magicabula AUAUA'),
        SelectField.Type.DEFAULT: StructField('I', default=0xabad1dea),
    }

    select = SelectField(DummyType, type2field)

    assert select.value == 0xabad1dea

    select = SelectField(DummyType, type2field, default=DummyType.SECOND)

    assert select.value == b'magicabula AUAUA'


def test_arrayfield():
    length = 10
    array = ArrayField(StructField('I'), n=length)

    # check some basic property
    assert isinstance(array.value, list)
    assert len(array.value) == length
    assert len(array) == length

    # check that the elements are not duplicated
    assert array[0] is not array[1]

    # check the offsets make sens
    assert array[0].offset == 0
    assert array[1].offset == 4
    assert array[9].offset == 36

    # check the value are all zero
    for _ in range(len(array)):
        field = array[_]
        assert field.value == 0

    # set one and check is actually changed
    array[3].value = 0xcafebabe
    assert [_.value for _ in array] == [
        0, 0, 0, 0xcafebabe, 0, 0, 0, 0, 0, 0,
    ]

    array.clear()

    assert len(array) == 0
