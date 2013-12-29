''' error.py -- Error and exception classes for Coconut
Author: Luke Williams <shmookey@shmookey.net>

Distributed under the MIT license, see LICENSE file for details.
'''

DEBUG = False
def debug(msg):
    if DEBUG: print (msg)

class DocumentNotFound (Exception):
    pass

class TransactionError (Exception):
    pass

#
# Validation Errors
#

class TypeMismatch (Exception):
    pass

class ValidationError (Exception):
    def __str__ (self):
        return '%s: %s' % (type(self).__name__,self.message)

class ValidationTypeError (ValidationError):
    def __init__ (self, expected, got):
        self.expected = expected
        self.got = got
        self.message = 'Expected %s, got %s' % (expected,got)
        debug(self.message)

class ValidationKeyError (ValidationError):
    def __init__ (self, key):
        self.key = key
        self.message = 'Unexpected key: %s' % key
        debug(self.message)

class ValidationListError (ValidationError):
    pass

class UniqueIndexViolation (ValidationError):
    pass

#
# Schema Errors
#

class SchemaError (Exception):
    def __str__ (self):
        return self.message

class SchemaUnknownType (SchemaError):
    def __init__ (self, schema):
        self.schema = schema
        self.message = 'Cannot determine type in schema %s' % schema
        debug(self.message)

class SchemaTypeError (SchemaError):
    def __init__ (self, schema, details):
        self.schema = schema
        self.message = 'Type error in schema %s. Details: %s' % (schema, details)
        debug(self.message)
        
class SchemaUnknownKey (SchemaError):
    def __init__ (self, key, schema):
        self.schema = schema
        self.key = key
        self.message = 'Unexpected key in schema: %s. Schema: %s.' % (key, schema)
        debug(self.message)
        
