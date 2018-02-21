

class Dependencies(object):
    '''This makes the relation between fields possible.

    We want that accessing this field the resolution is automagical.

    
    '''
    def __init__(self, expression):
        self.expression = expression
        self.dst = None
        self.src = None


# NOTE: we need the caller to seek() correctly a given offset
#       if it depends on external fields
class Offset(object):
    def __init__(self, expression):
        self.expression = expression

    def resolve(self, obj):
        # here split 'other_child.field'
        other_child, field_name = self.expression.split('.')
        sibiling = getattr(obj, other_child)

        return getattr(sibiling, field_name).value

