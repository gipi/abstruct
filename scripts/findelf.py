#!/usr/bin/env python3
'''
Reimplementation of the find(1) utilities but for file format. For now
it works only for ELF files but should not be too difficult to generalize.

TODO: implement common option such as
       - do not follow symlink
'''
import os
import sys
import logging
from pathlib import Path
from enum import Enum
from abstruct.executables import elf
from abstruct.enum import Compliant
from abstruct.exceptions import MagicException, ChunkUnpackException


logging.basicConfig(level=logging.DEBUG if 'DEBUG' in os.environ else logging.INFO)
logger = logging.getLogger(__name__)


def usage(progname):
    print(f'usage: {progname} [condition] [files...]')
    sys.exit(1)


def parse_file(path):
    try:
        victim = elf.ElfFile(path, compliant=Compliant.MAGIC)
    except (MagicException, FileNotFoundError, PermissionError, ChunkUnpackException, OSError):
        return None
    except Exception as e:
        logger.error(f'failed to handle file at path \'{path}\'', exc_info=True)
        return None

    return victim


if __name__ == '__main__':
    if len(sys.argv) < 3:
        usage(sys.argv[0])

    lhs, rhs = sys.argv[1].split('=')
    components = lhs.split('.')
    rhs = int(rhs)
    paths = sys.argv[2:]

    for basepath in paths:
        for path in Path(basepath).glob('**/*'):
            if not path.is_file():
                continue
            path = str(path.resolve())  # FIXME: in this way resolve symlinks and could be a problem
            logger.debug(path)

            victim = parse_file(path)

            if not victim:
                continue

            for component in components:
                victim = getattr(victim, component)

            value = victim.value if not isinstance(victim.value, Enum) else victim.value.value
            if value == rhs:
                print(path)
