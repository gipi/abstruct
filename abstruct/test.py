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
    ElfSectionType, ElfEIClass, ElfEIData, ElfSegmentType, ElfDynamicTagType,
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
    ZIPLocalFileHeader,
)

from .core import Chunk, Meta, Dependency, ChunkPhase
from .exceptions import AbstructException, MagicException
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
        self.assertTrue(isinstance(d.field, fields.StructField))
        self.assertEqual(len(d2._meta.fields), 1)

    def test_inheritance(self):
        '''subclasses inherit fields'''
        class Father(Chunk):
            field_a = fields.StringField(0x10)
            field_b = fields.StructField("I")

        class Son(Father):
            field_c = fields.StringField(0x08)

        field_b_value = b'\x01\x02\x03\x04'
        field_c_value = b'ABCDEFGH'
        son = Son(b'A' * 16 + field_b_value + field_c_value)

        fields_son = son.get_fields()

        self.assertEqual(len(fields_son), 3)
        self.assertEqual([_ for _ in fields_son], [
            'field_a', 'field_b', 'field_c',
        ])

        # check values make sense
        self.assertEqual(son.field_b.value, 0x04030201, f'field_b is {son.field_b.value:x}')
        self.assertEqual(son.field_c.value, field_c_value)

    def test_field_from_chunk(self):
        class Dummy(Chunk):
            field = fields.StructField('i')

        class DummyContainer(Chunk):
            dummy = Dummy()

        d = DummyContainer()

        self.assertTrue(hasattr(d, 'dummy'))
        self.assertTrue(hasattr(d.dummy, 'field'))

    def test_offset_basic(self):
        '''Test that the offset is handled correctly in basic case'''
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
        # type
        self.assertEqual(tlv.type.value, 0x01)
        self.assertEqual(tlv.type.offset, 0x00)
        # length
        self.assertEqual(tlv.length.value, 0x03)
        self.assertEqual(tlv.length.offset, 0x04)
        # data
        self.assertEqual(tlv.data.value, b'\x42' * 0x03)
        self.assertEqual(tlv.data.offset, 0x04 + 0x04)
        # extra
        self.assertEqual(tlv.extra.value, 0x0d0c0b0a)
        self.assertEqual(tlv.extra.offset, 0x04 + 0x04 + 0x03)

    def test_enum(self):
        self.assertTrue(ElfEIClass.ELFCLASS64.value == 2)
        self.assertEqual(ElfEIClass.ELFCLASS64.name, 'ELFCLASS64')

    def test_relayout(self):
        '''we want relayout'''
        class Dummy(Chunk):
            a = fields.StructField('I')
            b = fields.StructField('H')

        class Father(Chunk):
            dummy = Dummy()
            c     = fields.StringField(0x10)

        father = Father()

        father.dummy.a.value = 0xcafebabe
        father.dummy.b.value = 0x1dea
        father.c.value       = "A" * 10

        # before the relayout the offsets are not defined
        self.assertEqual(father.offset, None)
        self.assertEqual(father.dummy.offset, None)
        self.assertEqual(father.dummy.a.offset, None)
        self.assertEqual(father.dummy.b.offset, None)
        self.assertEqual(father.c.offset, None)

        # try to relayout all the world
        father.relayout()
        self.assertEqual(father.offset, 0)
        self.assertEqual(father.dummy.offset, 0)
        self.assertEqual(father.dummy.a.offset, 0)
        self.assertEqual(father.dummy.b.offset, 4)
        self.assertEqual(father.c.offset, 6)

    def test_unpacking_and_packing(self):
        class Dummy(Chunk):
            fieldA = fields.StructField('I')
            fieldB = fields.StructField('I')

        contents = b'\x01\x02\x03\x04\x0a\x0b\x0c\x0d'

        dummy = Dummy(contents)

        repacked_contents = dummy.pack()

        self.assertEqual(repacked_contents, contents)

    def test_packing_w_offset(self):
        '''check correctness packing when offset is indicated explicitely by a field'''
        class Dummy(Chunk):
            '''this format has 16 bytes located at the offset
            indicated in the first field'''
            off = fields.StructField('I')
            data = fields.StringField(0x10, offset=Dependency('off'))

        dummy = Dummy()

        # try to insert some values an then packing (w implicit relayouting)
        # I'm expecting to see the minimal offset (i.e. 4 bytes)
        dummy.data.value = b'\x41' * 0x10
        packed_contents = dummy.pack()

        # i'm expecting to see the AAAAs starting at offset 4
        self.assertEqual(dummy.off.value, 0x04)
        self.assertEqual(
            packed_contents,
            b'\x04\x00\x00\x00\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41'
        )
        # try to indicate explicitely the offset an then packing (wo relayouting)
        dummy.off.value = 0x0a

        # dummy.data.offset = 0x0a
        packed_contents = dummy.pack(relayout=False)

        # i'm expecting to see the AAAAs starting at offset 10
        self.assertEqual(dummy.off.value, 0x0a)
        self.assertEqual(
            packed_contents,
            b'\x0a\x00\x00\x00\x00\x00\x00\x00\x00\x00\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41'
        )

        # now we want a compliant file
        dummy.off.value = 0x0a
        packed_contents = dummy.pack()
        # i'm expecting to see the AAAAs starting at offset 10
        self.assertEqual(dummy.off.value, 0x04)
        self.assertEqual(
            packed_contents,
            b'\x04\x00\x00\x00\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41'
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

        df = DummyFile(b'\x01\x02\x03\x04\x05\x06\x07\x08')
        self.assertEqual(df.field_wo_default.value, 0x04030201)
        self.assertEqual(df.field_w_default.value, 0x08070605)

    def test_bitfield(self):
        class WhateverEnum(Enum):
            pass

    def test_array(self):
        class DummyChunk(Chunk):
            field_a = fields.StructField("I")
            field_b = fields.StructField("I")

        class DummyFile(Chunk):
            chunks = fields.ArrayField(DummyChunk(), n=3)

        d = DummyFile()

        self.assertTrue(hasattr(d, 'chunks'))
        self.assertEqual(len(d.chunks.value), 3)
        self.assertEqual(d.chunks.n, 3)
        self.assertTrue(isinstance(d.chunks.value, list))

        d.chunks.n = 0
        self.assertEqual(len(d.chunks.value), 0, 'check change in n -> change in array')

    def test_array_w_dependency(self):
        class Dummy(Chunk):
            count = fields.StructField('I')
            items = fields.ArrayField(fields.StructField('I'), n=Dependency('.count'))

        d = Dummy(b'\x05\x00\x00\x00' + b'A' * 4 + b'B' * 4 + b'C' * 4 + b'D' * 4 + b'E' * 4)

        self.assertEqual(d.count.value, 5)
        self.assertEqual(d.items.n, 5)
        self.assertEqual([_.value for _ in d.items.value], [
            0x41414141, 0x42424242, 0x43434343, 0x44444444, 0x45454545,
        ])

        # try to change 'n' and see what happens
        d.count.value = 3
        self.assertEqual(d.count.value, 3)
        self.assertEqual(d.items.n, 3)
        # self.assertEqual(len(d.items), 3)

        d.items.n = 4
        self.assertEqual(d.count.value, 4)
        self.assertEqual(d.items.n, 4)
        self.assertEqual(len(d.items), 4)

    def test_select(self):
        class DummyType(Flag):
            FIRST = 0
            SECOND = 1

        type2field = {
            DummyType.FIRST: (fields.StructField, ('I', ), {}),
            DummyType.SECOND: (fields.StringField, (0x10, ), {}),
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
            length = fields.StructField('I')
            garbage = fields.StringField(Dependency('.length'))

        dummy = DummyChunk()

        self.assertEqual(dummy.length.value, 0, f'check default \'length\' is zero')
        self.assertEqual(dummy.garbage.value, b'', f'check the starting string is empty')

        dummy.garbage.value = b'ABCD'
        self.assertEqual(dummy.length.value, 4, f'check we have an updated \'length\' field')

    def test_crc32(self):
        class DummyChunk(Chunk):
            dataA = fields.StructField('I')
            dataB = fields.StructField('I')
            dataC = fields.StructField('I')

            crc   = CRCField([
                'dataA',
                'dataC',
            ])

        dummy = DummyChunk()
        dummy.dataA.value = 0x01020304
        dummy.dataB.value = 0x05060708
        dummy.dataC.value = 0x090A0B0C

        dummy.pack()

        logger.debug(repr(dummy.crc))


class ELFTest(unittest.TestCase):

    def test_string_table(self):
        table = b'\x00ABCD\x00EFGH\x00'
        string_table = elf_fields.SectionStringTable(size=len(table))

        string_table.unpack(Stream(table))
        self.assertEqual(len(string_table.value), 3)
        self.assertEqual(string_table.value, [
            '',
            'ABCD',
            'EFGH',
        ])

        string_table = elf_fields.SectionStringTable(default=['', 'miao', 'bau'])
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
        elf.sections_header.append(str_header)

        self.assertEqual(elf.header.e_shnum.value, 1)
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
        self.assertEqual(type(elf.get_section_by_name('.strtab')), type(elf_fields.SectionStringTable()))

        # check if the string table is dumped correctly
        index_section_string_table = elf.header.e_shstrndx.value
        section_string_table = elf.sections_header.value[index_section_string_table]
        print(section_string_table.pack())
        print(elf.segments.get_segment_for_address(0x00001ef8))

        print(elf.dynamic)
        print(elf.dynamic[ElfDynamicTagType.DT_NEEDED])
        print(elf.dynamic.get(ElfDynamicTagType.DT_NEEDED))
        print(elf.dynamic.get(ElfDynamicTagType.DT_REL))
        print(elf.dynamic.get(ElfDynamicTagType.DT_PLTREL))

    def test_not_elf(self):
        '''if we try to parse a stream is not an ELF what happens?'''
        data_empty = b''
        data = b'\x7f\x45\x4c\x46\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00' + b'\x00' * 100

        empty_success = False
        try:
            elf = ElfFile(data_empty, compliant=Compliant.MAGIC)
        except MagicException as e:
            empty_success = True
        except Exception as e:
            logger.error(e)

        self.assertTrue(empty_success, 'check empty file causes exception')

        malformed_success = False
        try:
            elf = ElfFile(data, compliant=Compliant.ENUM | Compliant.MAGIC)
        except AbstructException as e:
            malformed_success = True
            logger.debug('error during parsing at field \'%s\'' % '.'.join(e.chain[::-1]))

        self.assertTrue(malformed_success, 'check ELF with magic but body malformed causes exceptiocheck ELF with magic but body malformed causes exceptionn')


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

        zp = ZIPLocalFileHeader(path_minimal)

        self.assertEqual(zp.filename.value, b"a/b")
