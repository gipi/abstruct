#!/usr/bin/env python3
'''
Reimplementation of the find(1) utilities but for file format.

TODO: implement common option such as
       - do not follow symlink
'''
import os
import sys
import importlib
import logging
from pathlib import Path
from enum import Enum
from abstruct.executables import elf
from abstruct.enum import Compliant
from abstruct.exceptions import MagicException, ChunkUnpackException


logging.basicConfig(level=logging.DEBUG if 'DEBUG' in os.environ else logging.INFO)
logger = logging.getLogger(__name__)


def usage(progname):
    print(f'''usage: {progname} [namespace] [object] [condition] [paths...]

The condition parameter can use the namespace by the variable "ns" and the parsed
object by the variable "obj". The path must be a directory.

For example

 $ find.py abstruct.executables.elf ElfFile obj.header.e_machine.value==ns.enum.ElfMachine.EM_386 /

will find all the ELF executables that target the i386 architecture.''')
    sys.exit(1)


def parse_file(cls, path):
    try:
        victim = cls(path, compliant=Compliant.MAGIC)
    except (MagicException, FileNotFoundError, PermissionError, ChunkUnpackException, OSError):
        return None
    except Exception as e:
        logger.error(f'failed to handle file at path \'{path}\'', exc_info=True)
        return None

    return victim


if __name__ == '__main__':
    if len(sys.argv) < 5:
        usage(sys.argv[0])

    ns = sys.argv[1]
    obj_name = sys.argv[2]

    ns = importlib.import_module(ns)

    conditions = sys.argv[3]
    paths = sys.argv[4:]

    cls = getattr(ns, obj_name)

    for basepath in paths:
        for path in Path(basepath).glob('**/*'):
            if not path.is_file():
                continue
            path = str(path.resolve())  # FIXME: in this way resolve symlinks and could be a problem
            logger.debug(path)

            obj = parse_file(cls, path)

            if not obj:
                continue

            code = compile(conditions, 'string', 'exec')
            if eval(code):
                print(path)
