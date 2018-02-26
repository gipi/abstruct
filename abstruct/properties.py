

class Dependency(object):
    '''This makes the relation between fields possible.

    We want that accessing this field the resolution is automagical.
    '''
    def __init__(self, expression, obj=None):
        self.expression = expression
        self.obj = obj

    def __call__(self, obj):
        return Dependency(self.expression, obj=obj)

    def _get_root(self, instance):
        is_root = False

        while not is_root:
            father = instance.father

            is_root = father.father is None

        return father

    def resolve(self, instance):
        '''With this method we resolve the attribute with respect to the instance
        passed as argument.'''
        field = None
        # here split the expression into the components
        # like python modules
        fields_path = self.expression.split('.') # FIXME: create class FieldPath to encapsulate

        if fields_path[0] != '.':
            field = self._get_root(instance)
            for component_name in fields_path:
                field = getattr(field, component_name)
        else:
            raise AttributeError('Dependency with relative expression not yer implemented!')

        return field.value


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

