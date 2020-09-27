'''
We are implementing fields to handle CRC calculation.
'''

from .. import fields

from zlib import crc32


# FIXME: if you don't pack the fields the CRC is undefined
#        maybe add a relationship between them
class CRCField(fields.StructField):
    """standard CRC methods with pre and post conditioning, as defined by ISO 3309 [ISO-3309]
    or ITU-T V.42 [ITU-V42]. The CRC polynomial employed is

      x^32+x^26+x^23+x^22+x^16+x^12+x^11+x^10+x^8+x^7+x^5+x^4+x^2+x+1

    The 32-bit CRC register is initialized to all 1's, and then the data from each byte is processed
    from the least significant bit (1) to the most significant bit (128). After all the data bytes are processed,
    the CRC register is inverted (its ones complement is taken). This value is transmitted (stored in the file)
    MSB first.

    For the purpose of separating into bytes and ordering, the least significant bit of the 32-bit CRC is defined to
    be the coefficient of the x^31 term.

    See <https://www.w3.org/TR/PNG-Structure.html#CRC-algorithm>.
    """

    def __init__(self, fields, *args, **kwargs):
        super().__init__('I', *args, **kwargs)
        self.fields = fields

    def calculate(self):
        value = b''
        for field_name in self.fields:
            field = getattr(self.father, field_name)
            value += field.raw

        return crc32(value)

    def _update_value(self):
        self.value = self.calculate()
