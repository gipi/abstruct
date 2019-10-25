class AbstructException(Exception):
    '''Base class to extend in order to throw exception in abstruct.

    It takes a single argument that represents the chain of the layer that
    caused the exception.
    '''

    def __init__(self, chain):
        self.chain = chain
        super().__init__()


class UnpackException(AbstructException):
    pass


class MagicException(AbstructException):
    pass


class ChunkUnpackException(AbstructException):
    pass


class UnrecoverableException(AbstructException):
    '''This is useful when is not possible to let an unknown value
    slip through the parsing.'''
    pass
