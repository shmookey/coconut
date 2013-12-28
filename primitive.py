''' primitive.py -- Coconut base classes.
Author: Luke Williams <shmookey@shmookey.net>

Distributed under the MIT license, see LICENSE file for details.
'''

class Element (object):
    '''Wrapper base class for basic types and references.'''
    pass

#
# Primitive types
#

class Str (Element, str):
    def __init__ (self, value):
        Element.__init__ (self)
        str.__init__(self, value)

class Int (Element, int):
    def __init__ (self, value):
        Element.__init__ (self)
        int.__init__(self, value)

class Float (Element, float):
    def __init__ (self, value):
        Element.__init__ (self)
        float.__init__(self, value)

class Timestamp (Int):
    pass

