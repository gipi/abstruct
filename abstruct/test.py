import logging
import os
import shutil
import subprocess
import tempfile
import unittest

from .elf import ElfFile, ElfType, ElfMachine, ElfSectionType
from .core import Chunk, Meta
from . import fields


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class CoreTests(unittest.TestCase):
    def test_meta(self):
        class Dummy(Chunk):
            field = fields.StructField('i')

        class Dummy2(Chunk):
            field2 = fields.StructField('i')

        d = Dummy()
        d2 = Dummy2()

        self.assertTrue(hasattr(d, '_meta'))
        self.assertTrue(isinstance(d._meta, Meta))
        self.assertEqual(len(d._meta.fields), 1)
        self.assertTrue(hasattr(d, 'field'))
        self.assertTrue(isinstance(d.field, fields.RealStructField))
        self.assertEqual(len(d2._meta.fields), 1)

    def test_chunk(self):
        class Dummy(Chunk):
            field = fields.StructField('i')

        class DummyContainer(Chunk):
            dummy = fields.DummyField()

        d = DummyContainer()


        self.assertTrue(hasattr(d, 'dummy'))
        self.assertTrue(hasattr(d.dummy, 'field'))

class FieldsTests(unittest.TestCase):
    def test_struct(self):
        class DummyFile(Chunk):
            field_wo_default = fields.StructField('I')
            field_w_default  = fields.StructField('I', default=0xdead)

        df = DummyFile()
        self.assertEqual(df.field_wo_default.value, 0)
        self.assertEqual(df.field_w_default.value, 0xdead)

    def test_array(self):
        class DummyChunk(Chunk):
            field_a = fields.StructField("I")
            field_b = fields.StructField("I")

        class DummyFile(Chunk):
            chunks = fields.ArrayField(DummyChunk, n=3)

        d = DummyFile()

        self.assertTrue(hasattr(d, 'chunks'))
        self.assertEqual(len(d.chunks.value), 3)
        self.assertTrue(isinstance(d.chunks.value, list))


class ELFTest(unittest.TestCase):
    def test_empty(self):
        elf = ElfFile()
        self.assertEqual(elf.elf_header.e_type.value, ElfType.ET_EXEC.value)

    def test_32bits(self):
        path_elf = os.path.join(os.path.dirname(__file__), 'main')

        logger.info(subprocess.check_output([
            'readelf',
            '-h',
            path_elf,
        ]).decode('utf-8'))

        elf = ElfFile(path_elf)

        self.assertEqual(elf.elf_header.e_type.value, ElfType.ET_DYN.value) # WHY IS COMPILED AS DYN? ALIENS!
        self.assertEqual(elf.elf_header.e_machine.value, ElfMachine.EM_386.value)
        self.assertEqual(elf.elf_header.e_shnum.value, 30)
        self.assertEqual(elf.sections.n, 30)
        self.assertEqual(len(elf.sections), 30)
        self.assertEqual(elf.sections.value[29].sh_type.value, ElfSectionType.SHT_STRTAB.value)
        self.assertEqual(elf.sections.value[28].sh_type.value, ElfSectionType.SHT_STRTAB.value)

