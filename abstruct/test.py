import logging
import os
import shutil
import subprocess
import tempfile
import unittest


from .executables.elf import (
    ElfFile,
    ElfType,
    ElfMachine,
    ElfSectionType, ElfEIClass, ElfEIData,
    SectionHeader)

from .images.png import (
    PNGHeader,
    PNGFile,
)

from .communications.stk500 import (
    STK500Packet,
    STK500CmdSignOnResponse,
)

from .core import Chunk, Meta, Dependency
from .streams import Stream
from . import fields


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class StreamTests(unittest.TestCase):
    def test_bytes_stream_read_all(self):
        data = b'\x01\x02\x03\x04\x05'

        stream = Stream(data)

        self.assertEqual(stream.read(1), b'\x01')
        self.assertEqual(stream.read(1), b'\x02')
        self.assertEqual(stream.read_all(), b'\x03\x04\x05')
        self.assertEqual(stream.tell(), 5)

    def test_file_stream_read_all(self):
        data = b'\x01\x02\x03\x04\x05'
        path_data = '/tmp/auaua'
        with open(path_data, 'wb') as f:
            f.write(data)

        stream = Stream(path_data)

        self.assertEqual(stream.read(1), b'\x01')
        self.assertEqual(stream.read(1), b'\x02')
        self.assertEqual(stream.read_all(), b'\x03\x04\x05')
        self.assertEqual(stream.tell(), 5)

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

class PaddingFieldTests(unittest.TestCase):
    def test_is_ok(self):
        class Padda(Chunk):
            padding = fields.PaddingField()

        contents = b'\x01\x02\x03\x04\x05'

        padda = Padda(contents)

        self.assertEqual(padda.padding.value, contents)

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

    def test_dependency(self):
        class DummyChunk(Chunk):
            magic = fields.StringField(n=5, default=b"HELLO")
            dummy_size = fields.StructField('<I', equals_to=Dependency('size'))

        dummy = DummyChunk()

        self.assertEqual(dummy.dummy_size.value, 9)

class ELFTest(unittest.TestCase):
    def test_empty(self):
        elf = ElfFile()
        self.assertEqual(elf.elf_header.e_type.value, ElfType.ET_EXEC.value)
        self.assertEqual(elf.elf_header.e_ehsize.value, 52)

    def test_minimal_from_zero(self):
        elf = ElfFile()
        str_header = SectionHeader()
        str_header.sh_type.value = ElfSectionType.SHT_STRTAB.value
        elf.sections.value.append(str_header)
        with open('/tmp/minimal', 'wb') as f:
            f.write(elf.pack())

    def test_32bits(self):
        path_elf = os.path.join(os.path.dirname(__file__), 'main')

        logger.info(subprocess.check_output([
            'readelf',
            '-h',
            path_elf,
        ]).decode('utf-8'))

        elf = ElfFile(path_elf)

        self.assertEqual(elf.elf_header.e_ident.EI_MAG0.value, b'\x7f')
        self.assertEqual(elf.elf_header.e_ident.EI_MAG1.value, b'E')
        self.assertEqual(elf.elf_header.e_ident.EI_MAG2.value, b'L')
        self.assertEqual(elf.elf_header.e_ident.EI_MAG3.value, b'F')
        self.assertEqual(elf.elf_header.e_ident.EI_CLASS.value, ElfEIClass.ELFCLASS32.value)
        self.assertEqual(elf.elf_header.e_ident.EI_DATA.value, ElfEIData.ELFDATA2LSB.value)


        self.assertEqual(elf.elf_header.e_type.value, ElfType.ET_DYN.value) # WHY IS COMPILED AS DYN? ALIENS!
        self.assertEqual(elf.elf_header.e_machine.value, ElfMachine.EM_386.value)
        self.assertEqual(elf.elf_header.e_ehsize.value, 52)
        self.assertEqual(elf.elf_header.e_shnum.value, 30)
        self.assertEqual(elf.elf_header.e_shstrndx.value, 29)
        self.assertEqual(elf.sections.n, 30)
        self.assertEqual(len(elf.sections), 30)
        self.assertEqual(elf.sections.value[29].sh_type.value, ElfSectionType.SHT_STRTAB.value)
        self.assertEqual(elf.sections.value[28].sh_type.value, ElfSectionType.SHT_STRTAB.value)

class STK500Tests(unittest.TestCase):
    def test_single(self):
        stk500_packet = b'\x1b\x04\x00\x05\x0e\x01\x02\x03\x04\x05\xff'

        packet = STK500Packet(stk500_packet)

        self.assertEqual(packet.message_start.value, 0x1b)
        self.assertEqual(packet.token.value, 0x0e)
        self.assertEqual(packet.message_size.value, 5)
        self.assertEqual(packet.message_body.value, b'\x01\x02\x03\x04\x05')

    def test_cmd_sign_on(self):
        cmd_sign_on_message_response = b'\x01\x00\x08\x41\x56\x52\x49\x53\x50\x5f\x32'

        message = STK500CmdSignOnResponse(cmd_sign_on_message_response)

        self.assertEqual(message.answer_id.value, 0x01)
        self.assertEqual(message.status.value, 0x00)
        self.assertEqual(message.signature_length.value, 8)
        self.assertEqual(message.signature.value, b"AVRISP_2")

class PNGTests(unittest.TestCase):
    def test_header(self):
        png_header = PNGHeader()

        self.assertEqual(png_header.magic.value, b'\x89PNG\x0d\x0a\x1a\x0a')

    def test_png_file(self):
        path_png = os.path.join(os.path.dirname(__file__), 'red.png')

        png = PNGFile(path_png)

        for idx, chunk in enumerate(png.chunks.value):
            print(idx, chunk, chunk.isCritical())

