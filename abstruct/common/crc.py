'''
We are implementing fields to handle CRC calculation.
'''

from .. import fields

from zlib import crc32


# FIXME: if you don't pack the fields the CRC is undefined
#        maybe add a relationship between them
class CRCField(fields.StructField):

    def __init__(self, fields, *args, **kwargs):
        self.fields = fields
        super().__init__('I', *args, **kwargs)

    def calculate(self):
        value = b''
        for field_name in self.fields:
            field = getattr(self.father, field_name)
            value += field.raw

        return crc32(value)

    def _update_value(self):
        self.value = self.calculate()
