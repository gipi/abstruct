import logging
from enum import Enum


class ChunkPhase(Enum):
    '''Enum to state the actual phase of a chunk'''
    INIT      = 0
    PROGRESS  = 1
    PACKING   = 2
    DONE      = 3


def get_root_from_chunk(instance):
    return get_instance_from_chunk(instance, condition=lambda x: x.father is None)


def get_instance_from_class_name(instance, name):
    return get_instance_from_chunk(instance, condition=lambda x: x.__class__.__name__ == name)


def get_instance_from_chunk(instance, condition):
    is_root = condition(instance)
    father = instance

    while not is_root:
        father = instance.father

        is_root = condition(father)
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
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

    def __call__(self, obj):
        return Dependency(self.expression, obj=obj)

    def resolve_field(self, instance):
        self.logger.debug('trying to resolve \'%s\'' % self.expression)
        field = None
        # here split the expression into the components
        # like python modules
        fields_path = self.expression.split('.')  # FIXME: create class FieldPath to encapsulate

        # find the root the resolution starts
        if fields_path[0] != '':
            if fields_path[0].startswith('@'):  # we want to resolve wrt a class
                class_name = fields_path[0][1:]
                self.logger.debug('resolve from class name: \'%s\'' % class_name)
                field = get_instance_from_class_name(instance, class_name)

                fields_path = fields_path[1:]  # skip the first one that is already resolved
            else:
                field = get_root_from_chunk(instance)
                self.logger.debug('resolve from root: \'%s\'' % field.__class__.__name__)
        else:  # we have a relative dependency
            field = instance.father
            self.logger.debug('resolve from father: \'%s\'' % field.__class__.__name__)
            fields_path = fields_path[1:]  # skip the first one that is empty

        # now we can resolve each component
        for component_name in fields_path:
            field = getattr(field, component_name)
        self.logger.debug('resolved as field %s' % field.__class__.__name__)

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

        self.logger.debug('resolved with value %s' % value)

        return value


class RatioDependency(Dependency):

    def __init__(self, ratio, expression, obj=None):
        super().__init__(expression, obj)
        self._ratio = ratio

    def resolve(self, instance):
        value = super().resolve(instance)

        return int(value / self._ratio)


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
