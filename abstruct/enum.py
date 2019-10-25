from enum import Flag


class Compliant(Flag):
    '''It indicates which degree of compliantness the data must reflect the format'''
    NONE  = 0
    ENUM  = 1 << 0
    MAGIC = 1 << 1
    INHERIT = 1 << 2
