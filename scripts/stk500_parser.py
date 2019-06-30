import sys
import logging


from abstruct.communications.stk500 import STK500Packet
from abstruct.core import *
from abstruct import fields


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class STK500Conversation(Chunk):
    whatever = fields.StructField('I', little_endian=False)
    packets  = fields.ArrayField(STK500Packet, n=10)


if __name__ == '__main__':
    path = sys.argv[1]

    conversation = STK500Conversation(path)

    print('%08x' % conversation.whatever.value)
    print(conversation.packets.value)

    for message in conversation.packets.value:
        print(message)

    import ipdb;ipdb.set_trace()
