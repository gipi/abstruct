from abstruct.core import Chunk
from abstruct.fields import StructField, StringField
from abstruct.properties import Dependency


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
    assert dummy.a.father == dummy

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


def test_chunk_w_dependencies():
    class Example(Chunk):
        sz = StructField('I')
        data = StringField(Dependency('.sz'), default=b'kebab')

    example = Example()

    assert list(example.get_dependencies().keys()) == [
        'data.length',
    ]

    assert example.sz.father == example
    assert example.sz.value == 5
    assert example.data.value == b'kebab'


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
