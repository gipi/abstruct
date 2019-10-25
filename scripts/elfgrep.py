#!/usr/bin/env python3
import os
import sys
import logging
from enum import Enum
from abstruct.executables import elf
from abstruct.enum import Compliant


logging.basicConfig(level=logging.DEBUG if 'DEBUG' in os.environ else logging.INFO)
logger = logging.getLogger(__name__)


def usage(progname):
    print(f'usage: {progname} [condition] [files...]')
    sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        usage(sys.argv[0])

    lhs, rhs = sys.argv[1].split('=')
    components = lhs.split('.')
    rhs = int(rhs)
    paths = sys.argv[2:]

    for path in paths:
        try:
            victim = elf.ElfFile(path, compliant=Compliant.MAGIC)
        except:
            continue
        for component in components:
            victim = getattr(victim, component)

        value = victim.value if not isinstance(victim.value, Enum) else victim.value.value
        if value == rhs:
            print(path)
        # print(victim)
