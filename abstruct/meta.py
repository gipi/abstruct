import copy
import logging
from enum import Enum, auto


class Endianess(Enum):
    LITTLE_ENDIAN = auto()
    BIG_ENDIAN    = auto()
    NETWORK       = auto()
    NATIVE        = auto()


class FieldDescriptor(object):
    """Wrapper around field access of a Field related class."""

    def __init__(self, field_instance: "Field", field_name: str):
        self.logger = logging.getLogger(f"{self.__module__}.{self.__class__.__name__}")
        self.field = field_instance
        self.field.name = field_name

    def __get__(self, instance, type=None):
        # NOTE: here we don't have yet initialized the instance so it's possible to fail
        self.logger.debug("__get__ from %s for field named '%s'", instance.__class__.__name__, self.field.name)
        data = instance.__dict__

        if self.field.name in data:
            return data[self.field.name]
        else:
            self.logger.debug("create new field for field named '%s'", self.field.name)
            new_field = self.field.create(father=instance)
            data[self.field.name] = new_field
            return data[self.field.name]

    def __set__(self, instance, value):
        self.logger.debug("__set__ from {} for field named '%s'", instance, self.field.name)
        data = instance.__dict__

        # if the value is the same type then set as it is
        if isinstance(value, self.field.__class__):
            value.father = instance
            value.name = self.field.name
            data[self.field.name] = value
        # otherwise delegate to the field
        else:
            data[self.field.name].set(value)


class FieldBase(object):

    def contribute_to_chunk(self, cls, name):
        if not getattr(cls, name, None):
            setattr(cls, name, FieldDescriptor(self, name))
        else:
            raise AttributeError(f'field {name} is already present in class {cls.__name__}')

    def create(self, father):
        instance = copy.deepcopy(self)
        instance.father = father
        return instance


class Meta(object):
    """Class containing metadata about the abstraction"""

    def __init__(self):
        self.fields = []


class MetaChunk(type):

    def __new__(cls, names, bases, attrs):
        '''All of this is a big hack, maybe too inspired by how Django does a similar thing!'''
        module = attrs.pop('__module__')
        classcell = attrs.pop('__classcell__', None)

        new_attrs = {
            '__module__': module,
        }
        if classcell is not None:
            new_attrs['__classcell__'] = classcell
        new_cls = super(MetaChunk, cls).__new__(cls, names, bases, new_attrs)

        new_cls._meta = Meta()

        # handle inheritance
        parents = [_ for _ in bases if isinstance(_, MetaChunk)]
        for parent in parents:
            for obj_name in parent._meta.fields:
                obj = parent.__dict__[obj_name]
                setattr(new_cls, obj_name, obj)
                new_cls._meta.fields.append(obj_name)

        for obj_name, obj in attrs.items():
            new_cls.add_to_class(obj_name, obj)

        cls.logger = logging.getLogger(__name__)

        return new_cls

    def add_to_class(cls, name, value):
        if hasattr(value, 'contribute_to_chunk'):
            cls.logger.debug('contribute_to_chunk() found for field \'%s\'' % name)
            cls._meta.fields.append(name)
            value.contribute_to_chunk(cls, name)
        else:
            setattr(cls, name, value)
