import logging
import os
import shutil
import subprocess
import tempfile
import unittest

from .elf import ElfFile


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ELFTest(unittest.TestCase):
    def setUp(self):
        self.path = tempfile.mkdtemp()
        logger.debug('creating temp path = \'%s\'' % self.path)

    def tearDown(self):
        logger.debug('removing path \'%s\'' % self.path)
        #shutil.rmtree(self.path)

    def test_empty(self):
        elf = ElfFile()

    def test_32bits(self):
        code = '''
#include <stdio.h>

int main() {
    return 0;
}
'''
        path_c_file = os.path.join(self.path, 'main.c')
        path_exe    = os.path.join(self.path, 'main')
        with open(path_c_file, 'w') as f:
            f.write(code)

        process = subprocess.Popen([
            'gcc',
            '-m32',
            path_c_file,
            '-o',
            path_exe,
        ])
        process.wait()

        logger.info(subprocess.check_output([
            'readelf',
            '-h',
            path_exe,
        ]).decode('utf-8'))

        elf = ElfFile(path_exe)

        self.assertEqual(elf.elf_header.e_type.value, 0x03)
        self.assertEqual(elf.elf_header.e_machine.value, 0x03)
