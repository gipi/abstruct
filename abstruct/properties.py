import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def get_root_from_chunk(instance):
    is_root = instance.father is None
    father = instance

    while not is_root:
        father = instance.father

        is_root = father.father is None
        instance = father

    return father

class Dependency(object):
    '''This makes the relation between fields possible.

    We want that accessing this field the resolution is automagical.

    The relation is defined in one direction (usually for unpacking) and
    must be reversed during the packing phase!

    Probably right now is overcomplicated, we want to understand if make sense
    to use __getattribute__ and __setattr__ to resolve automagically.
    '''
    def __init__(self, expression, obj=None):
        self.expression = expression
        self.obj = obj

    def __call__(self, obj):
        return Dependency(self.expression, obj=obj)

    def resolve_field(self, instance):
        logger.debug('trying to resolve \'%s\'' % self.expression)
        field = prev_field = None
        # here split the expression into the components
        # like python modules
        fields_path = self.expression.split('.') # FIXME: create class FieldPath to encapsulate

        if fields_path[0] != '':
            field = get_root_from_chunk(instance)
            for component_name in fields_path:
                field = getattr(field, component_name)
        else:
            raise AttributeError('Dependency with relative expression not yet implemented!')

        return field

    def resolve(self, instance):
        '''With this method we resolve the attribute with respect to the instance
        passed as argument.'''
        field = self.resolve_field(instance)

        import inspect

        value = None

        if inspect.ismethod(field):
            value = field()
        else:
            value = field.value

        logger.debug('resolved with value %s' % value)

        return value


# NOTE: we need the caller to seek() correctly a given offset
#       if it depends on external fields
#       It's different with respect to Dependency() since
#       the expression is with respect to the father (probably
#       to be fixed)
class Offset(object):
    def __init__(self, expression):
        self.expression = expression

    def resolve(self, obj):
        # here split 'other_child.field'
        other_child, field_name = self.expression.split('.')
        sibiling = getattr(obj, other_child)

        return getattr(sibiling, field_name).value

