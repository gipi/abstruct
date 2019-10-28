import logging
import os
import subprocess
import unittest
from enum import Flag, Enum
from .enum import Compliant


from .executables.elf import (
    ElfFile,
    SectionHeader,
    elf_fields,
)
from .executables.elf.enum import (
    ElfType,
    ElfMachine,
    ElfSectionType, ElfEIClass, ElfEIData, ElfSegmentType,
)

from .images.png import (
    PNGColorType,
    PNGHeader,
    PNGFile,
)

from .communications.stk500 import (
    STK500Packet,
    STK500CmdSignOnResponse,
)

from .common.crc import (
    CRCField,
)

from .compression.zip import (
    ZIPHeader,
)

from .core import Chunk, Meta, Dependency, ChunkPhase
from .exceptions import AbstructException
from .streams import Stream
from . import fields


logging.basicConfig(level=logging.DEBUG if 'DEBUG' in os.environ else logging.INFO)
logger = logging.getLogger(__name__)


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
        self.assertEqual(d.phase, ChunkPhase.DONE)
        self.assertEqual(d.dummy.phase, ChunkPhase.DONE)
        self.assertEqual(d.dummy.field.phase, ChunkPhase.INIT)

    def test_offset_basic(self):
        '''Test that the offset is handled correctly'''
        class Dummy(Chunk):
            field1 = fields.StringField(0x2)
            field2 = fields.StringField(0x3)

        dummy = Dummy(b'\x01\x02\x0a\x0b')

        self.assertEqual(dummy.field1.value, b'\x01\x02')
        self.assertEqual(dummy.field2.value, b'\x0a\x0b')
        # we expect the offset to be present
        self.assertEqual(dummy.field1.offset, 0)
        self.assertEqual(dummy.field2.offset, 2)

    def test_offset_dependencies(self):
        class TLV(Chunk):
            type   = fields.StructField('I')
            length = fields.StructField('I')
            data   = fields.StringField(Dependency('length'))
            extra  = fields.StructField('I')

        tlv = TLV((
            b'\x01\x00\x00\x00'
            b'\x0f\x00\x00\x00'
            b'\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41'
            b'\x0a\x0b\x0c\x0d'
        ))

        self.assertEqual(tlv.type.value, 0x01)
        self.assertEqual(tlv.type.offset, 0x00)
        self.assertEqual(tlv.length.value, 0x0f)
        self.assertEqual(tlv.length.offset, 0x04)
        self.assertEqual(tlv.data.value, b'\x41' * 0x0f)
        self.assertEqual(tlv.data.offset, 0x04 + 0x04)
        self.assertEqual(tlv.extra.value, 0x0d0c0b0a)
        self.assertEqual(tlv.extra.offset, 0x04 + 0x04 + 0x0f)

        # now try to change the data field's size and verify that
        # the offset for extra is recalculated and the size field
        # also is updated accordingly
        tlv.data.value = b'\x42\x42\x42'
        tlv.relayout()  # we must trigger relayouting
        tlv.pack()
        self.assertEqual(tlv.type.value, 0x01)
        self.assertEqual(tlv.type.offset, 0x00)
        self.assertEqual(tlv.length.value, 0x03)
        self.assertEqual(tlv.length.offset, 0x04)
        self.assertEqual(tlv.data.value, b'\x42' * 0x03)
        self.assertEqual(tlv.data.offset, 0x04 + 0x04)
        self.assertEqual(tlv.extra.value, 0x0d0c0b0a)
        self.assertEqual(tlv.extra.offset, 0x04 + 0x04 + 0x03)

    def test_enum(self):
        self.assertTrue(ElfEIClass.ELFCLASS64.value == 2)
        self.assertEqual(ElfEIClass.ELFCLASS64.name, 'ELFCLASS64')

    def test_packing(self):
        class Dummy(Chunk):
            fieldA = fields.StructField('I')
            fieldB = fields.StructField('I')

        contents = b'\x01\x02\x03\x04\x0a\x0b\x0c\x0d'

        dummy = Dummy(contents)

        repacked_contents = dummy.pack()

        self.assertEqual(repacked_contents, contents)

    def test_packing_w_offset(self):
        class Dummy(Chunk):
            '''this format has 16 bytes located at the offset
            indicated in the first field'''
            off = fields.StructField('I')
            data = fields.StringField(0x10, offset=Dependency('off'))

        dummy = Dummy()

        # try to insert some values an then packing
        dummy.data.value = b'\x41' * 0x10
        packed_contents = dummy.pack()

        # i'm expecting to see the AAAAs starting at offset 4
        self.assertEqual(dummy.off.value, 0x04)
        self.assertEqual(
            packed_contents,
            b'\x0a\x00\x00\x00\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41'
        )
        # try to insert some values an then packing
        dummy.off.value = 0x0a

        # dummy.data.offset = 0x0a
        packed_contents = dummy.pack()

        # i'm expecting to see the AAAAs starting at offset 4
        self.assertEqual(dummy.off.value, 0x04)
        self.assertEqual(
            packed_contents,
            b'\x0a\x00\x00\x00\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41'
        )

        # now we don't want a compliant file
        packed_contents = dummy.pack()
        dummy.off.value = 0x0a
        # i'm expecting to see the AAAAs starting at offset 10
        self.assertEqual(dummy.off.value, 0x0a)
        self.assertEqual(
            packed_contents,
            b'\x0a\x00\x00\x00\x00\x00\x00\x00\x00\x00\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41'
        )


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

    def test_bitfield(self):
        class WhateverEnum(Enum):
            pass

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

    def test_select(self):
        class DummyType(Flag):
            FIRST = 0
            SECOND = 1

        type2field = {
            DummyType.FIRST: (fields.RealStructField, ('I', ), {}),
            DummyType.SECOND: (fields.RealStringField, (0x10, ), {}),
        }

        class DummyChunk(Chunk):
            type = fields.StructField('I', enum=DummyType)
            data = fields.SelectField('type', type2field)

        dummy = DummyChunk()

        # first we try to unpack the FIRST type
        data = b'\x00\x00\x00\x00\x01\x02\x03\x04'
        dummy.unpack(Stream(data))

        self.assertEqual(dummy.type.value, DummyType.FIRST)
        self.assertEqual(dummy.data.value, 0x04030201)

        # then we try the SECOND type
        data = b'\x01\x00\x00\x00\x0f\x0e\x0d\x0c\x0b\x0a\x09\x08\x07\x06\x05\x04\x03\x02\x01\x00'
        dummy.unpack(Stream(data))

        self.assertEqual(dummy.type.value, DummyType.SECOND)
        self.assertEqual(dummy.data.value, b'\x0f\x0e\x0d\x0c\x0b\x0a\x09\x08\x07\x06\x05\x04\x03\x02\x01\x00')

    def test_dependency(self):
        class DummyChunk(Chunk):
            magic = fields.StringField(n=5, default=b"HELLO")
            garbage = fields.StringField(0x10)
            dummy_size = fields.StructField('I', equals_to=Dependency('size'))

        dummy = DummyChunk()

        self.assertEqual(dummy.dummy_size.value, 25)

        dummy.garbage.value = b'ABCD'
        self.assertEqual(dummy.dummy_size.value, 13)

    def test_crc32(self):
        class DummyChunk(Chunk):
            dataA = fields.StructField('I')
            dataB = fields.StructField('I')
            dataC = fields.StructField('I')

            crc   = CRCField([
                'dataA',
                'dataC',
            ], formatter='0x%08x')

        dummy = DummyChunk()
        dummy.dataA.value = 0x01020304
        dummy.dataB.value = 0x05060708
        dummy.dataC.value = 0x090A0B0C

        dummy.pack()

        logger.debug(repr(dummy.crc))


class ELFTest(unittest.TestCase):

    def test_string_table(self):
        table = b'\x00ABCD\x00EFGH\x00'
        string_table = elf_fields.RealSectionStringTable(size=len(table))

        string_table.unpack(Stream(table))
        self.assertEqual(len(string_table.value), 3)
        self.assertEqual(string_table.value, [
            '',
            'ABCD',
            'EFGH',
        ])

        string_table = elf_fields.RealSectionStringTable(default=['', 'miao', 'bau'])
        s = Stream(b'')
        string_table.pack(s)

        self.assertEqual(s.getvalue(), b'\x00miao\x00bau\x00')

    def test_empty(self):
        elf = ElfFile()
        self.assertEqual(elf.header.e_type.value, ElfType.ET_EXEC)
        self.assertEqual(elf.header.e_ehsize.value, 52)

    def test_minimal_from_zero(self):
        elf = ElfFile()
        str_header = SectionHeader(father=elf)
        str_header.sh_type.value = ElfSectionType.SHT_STRTAB
        elf.sections_header.value.append(str_header)
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

        self.assertEqual(elf.header.e_ident.EI_MAG0.value, b'\x7f')
        self.assertEqual(elf.header.e_ident.EI_MAG1.value, b'E')
        self.assertEqual(elf.header.e_ident.EI_MAG2.value, b'L')
        self.assertEqual(elf.header.e_ident.EI_MAG3.value, b'F')
        self.assertEqual(elf.header.e_ident.EI_CLASS.value, ElfEIClass.ELFCLASS32)
        self.assertEqual(elf.header.e_ident.EI_DATA.value, ElfEIData.ELFDATA2LSB)

        self.assertEqual(elf.header.e_machine.value, ElfMachine.EM_386)
        self.assertEqual(elf.header.e_type.value, ElfType.ET_DYN)  # WHY IS COMPILED AS DYN? ALIENS!

        # sections
        SECTIONS_NUMBER = 30
        self.assertEqual(elf.header.e_ehsize.value, 52)
        self.assertEqual(elf.sections_header.n, SECTIONS_NUMBER)
        self.assertEqual(elf.header.e_shnum.value, SECTIONS_NUMBER)
        self.assertEqual(elf.header.e_shstrndx.value, 29)
        self.assertEqual(len(elf.sections_header), SECTIONS_NUMBER)
        self.assertEqual(len(elf.sections.value), SECTIONS_NUMBER)
        self.assertEqual(elf.sections_header.value[29].sh_type.value, ElfSectionType.SHT_STRTAB)
        self.assertEqual(elf.sections_header.value[29].offset, 7212)
        self.assertEqual(elf.sections_header.value[28].sh_type.value, ElfSectionType.SHT_STRTAB)
        # programs
        self.assertEqual(elf.header.e_phentsize.value, 32)
        self.assertEqual(elf.header.e_phnum.value, 9)
        self.assertEqual(len(elf.segments_header), 9)
        self.assertEqual(  # we remove the last three elements since have not well defined type
            [_.p_type.value for _ in elf.segments_header.value[:-3]],
            [_ for _ in [
                ElfSegmentType.PT_PHDR,
                ElfSegmentType.PT_INTERP,
                ElfSegmentType.PT_LOAD,
                ElfSegmentType.PT_LOAD,
                ElfSegmentType.PT_DYNAMIC,
                ElfSegmentType.PT_NOTE,
            ]],
        )
        self.assertEqual(elf.section_names, [
            '',
            '.interp',
            '.note.ABI-tag',
            '.note.gnu.build-id',
            '.gnu.hash',
            '.dynsym',
            '.dynstr',
            '.gnu.version',
            '.gnu.version_r',
            '.rel.dyn',
            '.rel.plt',
            '.init',
            '.plt',
            '.plt.got',
            '.text',
            '.fini',
            '.rodata',
            '.eh_frame_hdr',
            '.eh_frame',
            '.init_array',
            '.fini_array',
            '.dynamic',
            '.got',
            '.got.plt',
            '.data',
            '.bss',
            '.comment',
            '.symtab',
            '.strtab',
            '.shstrtab',
        ])
        self.assertEqual(elf.section_names[14], '.text')
        self.assertEqual(len(elf.symbol_names), 33)
        self.assertEqual(elf.symbols['main'].st_shndx.value, 14)
        print(elf.symbols)

        print(elf.dyn_symbols)

        print(elf.sections_header.value[14])
        from .executables.elf.code import disasm, CS_MODE_32, CS_ARCH_X86
        dot_text_starting_offset = elf.sections_header.value[14].sh_addr.value
        print('\n'.join(
            ["0x%x:\t%s\t%s" % (_.address, _.mnemonic, _.op_str)
                for _ in disasm(elf.get_section_by_name('.text').value, CS_ARCH_X86, CS_MODE_32, start=dot_text_starting_offset)]))
        self.assertEqual(type(elf.get_section_by_name('.strtab')), type(elf_fields.RealSectionStringTable()))

        # check if the string table is dumped correctly
        index_section_string_table = elf.header.e_shstrndx.value
        section_string_table = elf.sections_header.value[index_section_string_table]
        print(section_string_table.pack())
    def test_not_elf(self):
        '''if we try to parse a stream is not an ELF what happens?'''
        data = b'\x0f\x45\x4c\x46\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00' + b'\x00' * 100
        data = b'miao' * 16

        try:
            elf = ElfFile(data, compliant=Compliant.ENUM | Compliant.MAGIC)
        except AbstructException as e:
            logger.debug('error during parsing at field \'%s\'' % '.'.join(e.chain[::-1]))

        elf = ElfFile(data, complaint=Compliant.MAGIC)


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

        self.assertEqual(png.chunks.value[0].type.value, b'IHDR')
        self.assertEqual(png.chunks.value[0].Data._field.color.value, PNGColorType.RGB_PALETTE)

        for idx, chunk in enumerate(png.chunks.value):
            print(idx, chunk, chunk.isCritical(), chunk.crc.calculate())


class ZIPTests(unittest.TestCase):

    def test_minimal(self):
        path_minimal = os.path.join(os.path.dirname(__file__), '..', 'extra', 'minimal.zip')

        zp = ZIPHeader(path_minimal)

        print(zp)
