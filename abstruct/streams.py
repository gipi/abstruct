import io
import logging

from .properties import Offset


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Stream(object):
    '''This is a simple wrapper around String/File object to
    uniform its properties: mainly we need to have a seek() method
    that handles correctly Offset() instances.'''
    def __init__(self, obj, flags='r'):
        '''Here we normalize the object in order to be accessed as a normal file object'''
        self._type = type(obj)
        self.flags = flags # this probably need to be a more elaborate value (like mmap)
        self.obj = obj
        self.history = []

        init_method_name = 'init_%s' % self.obj.__class__.__name__

        init_method = getattr(self, init_method_name)

        init_method()

    def __getattr__(self, name):
        return getattr(self.obj, name)

    def __del__(self):
        self.obj.close()

    def init_str(self):
        '''We think this is a path'''
        logger.debug('opening path \'%s\'' % self.obj)
        self.obj = open(self.obj, 'rb')

    def init_bytes(self):
        '''We think these are raw bytes'''
        self.obj = io.BytesIO(self.obj)

    def seek(self, offset):
        real_offset = None

        if isinstance(offset, Offset):
            real_offset = offset.resolve()
        elif isinstance(offset, int):
            real_offset = offset
        else:
            raise ValueError('\'%s\' is the wrong kind of offset to use' % offset.__class__.__name__)

        self.obj.seek(real_offset)

    def read_all(self):
        '''Here we try to implement a method that returns all the data possible
        FIXME: find a better way to do this.
        '''
        data = []
        is_there_more = True
        while is_there_more:
            b = self.read(1)
            is_there_more = (len(b) != 0)
            data.append(b)

        return b''.join(data)

    def write(self, data):
        return self.obj.write(data)

    # TODO: create contextmanager
    def save(self):
        self.history.append(self.obj.tell())

    def restore(self):
        old_seek = self.history.pop()
        self.obj.seek(old_seek)
