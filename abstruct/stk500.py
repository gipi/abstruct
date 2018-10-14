'''
Description of STK500 Communication protocol.

http://ww1.microchip.com/downloads/en/AppNotes/doc2591.pdf
'''
from .core import *
from . import fields

class STK500Packet(Chunk):
    '''Transport layer'''
    message_start   = fields.StructField('B', default=0x1b, formatter='%02x')
    sequence_number = fields.StructField('B')
    message_size    = fields.StructField('H', little_endian=False)
    token           = fields.StructField('B', default=0x0e, formatter='%02x')
    message_body    = fields.StringField(Dependency('message_size'))
    checksum        = fields.StructField('B', formatter='%02x')

'''
Application layer
'''
class STK500CmdSignOnResponse(Chunk):
    answer_id = fields.StructField('B')
    status    = fields.StructField('B')
    signature_length = fields.StructField('B')
    signature = fields.StringField(Dependency('signature_length'))
