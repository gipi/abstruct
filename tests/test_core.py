from abstruct.core import Chunk
from abstruct.fields import StructField, StringField


def test_conversion_raw_value():
    """Check that the attributes "value" and "raw" are the analogous
    of the integers and bytes representation for a field.

    NOTE: this should be done for all the fields."""
    field = StructField('I')

    assert field.value == 0
    assert field.raw == b'\x00'

    field.value = 0xcafe

    assert field.value == 0xcafe
    assert field.raw == b'\xfe\xca'


def test_proxy_like_format():
    """Check that a file format having sub-components referring to overlapping data
    behaves gently.

    Some formats (ELF *cough*) have different sub-components that refer to the same underlying
    data, often with different representation of it.
    """
    class Proxy(Chunk):
        off = StructField('I')
        sz  = StructField('I')

    class Experiment(Chunk):
        """
        Simple file format where two header-like fields intercept overlapping data into the file.
        """
        proxy_a = Proxy()
        proxy_b = Proxy()

        contents = StringField(0x100)

    experiment = Experiment()

    assert experiment.size() == 0x100 + 2 * (4 + 4)
    assert experiment.value == b'\x00' * experiment.size()
