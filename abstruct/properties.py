import logging
from enum import Enum, auto
from functools import lru_cache
import inspect
from typing import List, Tuple, Type


class ChunkPhase(Enum):
    '''Enum to state the actual phase of a chunk'''
    INIT      = 0
    PROGRESS  = auto()
    RELAYOUTING = auto()
    PACKING   = auto()
    UNPACKING = auto()
    DONE      = auto()


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


class Dependency:
    '''This makes the relation between fields possible.

    We want that accessing this field the resolution is automagical.

    The relation is defined in one direction (usually for unpacking) and
    must be reversed during the packing phase!

    In practice this class allows to write something like

        class Simple(Chunk):
            length = fields.StructField('I')
            data = fields.StringField(n=Dependency('.length'))

    and have the (internal) length of the string contained in the field named 'data'
    strictly connected to the field named 'length'.

    The syntax for defining the expression is inspired from module resolution
    with an extra element via the first char of the expression: we have the following

     - '.' indicates we refer to a field at the same level
     - '@' indicates the the first component is the name of a class
     - '#' indicates that an actual instance

    Probably right now is overcomplicated, we want to understand if make sense
    to use __getattribute__ and __setattr__ to resolve automagically.
    '''
    def __init__(self, expression, obj: Type["Field"] = None):
        self.expression = expression
        self.obj = obj
        self.logger = logging.getLogger(__name__)
        self._hierarchy: List["Field"] = []

    def __repr__(self):
        return f'<{self.__class__.__name__}({self.expression})>'

    def __call__(self, obj):
        return Dependency(self.expression, obj=obj)

    def _resolve_wrt_class(self, instance: Type["Field"], fields_path: List[str]) -> Tuple[Type["Field"], List[str]]:
        class_name = fields_path[0][1:]
        self.logger.debug('resolve from class name: \'%s\'' % class_name)
        field = get_instance_from_class_name(instance, class_name)

        fields_path = fields_path[1:]  # skip the first one that is already resolved

        return field, fields_path

    def _resolve_wrt_instance(self, fields_path: List[str]) -> Tuple[Type["Field"], List[str]]:
        self.logger.debug("trying to resolve wrt of an instance '%s'" % self.expression)
        if self.obj is None:
            raise AttributeError("I could not use resolution with respect to instance since 'obj' is not initialized")

        fields_path = fields_path[0][1:], *fields_path[1:]
        return self.obj, fields_path

    def resolve_field(self, instance):
        self.logger.debug('trying to resolve \'%s\' using class \'%s\'' % (
            self.expression,
            self.__class__.__name__,
        ))

        self._hierarchy = []

        field = None
        # here split the expression into the components
        # like python modules
        fields_path = self.expression.split('.')  # FIXME: create class FieldPath to encapsulate
        # '.miao'.split(".") -> ['', 'miao']
        # 'miao'.split(".") -> ['miao']

        # find the root the resolution starts
        if fields_path[0] != '':
            if fields_path[0].startswith('@'):  # we want to resolve wrt a class
                field, fields_path = self._resolve_wrt_class(instance, fields_path)
            elif fields_path[0].startswith('#'):
                field, fields_path = self._resolve_wrt_instance(fields_path)
            else:
                field = get_root_from_chunk(instance)
                self.logger.debug(' resolve from root: \'%s\'' % field.__class__.__name__)
        else:  # we have a relative dependency
            field = instance.father
            self.logger.debug(' resolve from father: \'%s\'' % field.__class__.__name__)
            fields_path = fields_path[1:]  # skip the first one that is empty

        self._hierarchy.append(field)

        # now we can resolve each component
        for component_name in fields_path:
            field = getattr(field, component_name)
            self.logger.debug(' resolved sub-component "%s" from "%s"' % (
                field.__class__.__name__, component_name))
            self._hierarchy.append(field)

        self.logger.debug(' resolved as field %s' % field.__class__.__name__)

        return field

    def _do_resolve(self, instance):
        value = None

        field = self._hierarchy[-1]

        if inspect.ismethod(field):
            value = field()
        else:
            value = field.value

        self.logger.debug(' resolved with value %s' % value)

        return value

    # @lru_cache()
    def resolve(self, instance):
        '''With this method we resolve the attribute with respect to the instance
        passed as argument.'''
        self.resolve_field(instance)

        return self._do_resolve(instance)

    def _do_value(self, instance, value):
        """Returns the value to be set"""
        return value

    def resolve_and_set(self, instance, value):
        """Set the value"""
        real_field = self.resolve_field(instance)
        if not hasattr(real_field, 'value'):
            raise ValueError(f'something is wrong with the Dependency resolution!')
        real_field.value = self._do_value(instance, value)

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
