''' error.py -- Error and exception classes for Coconut
Author: Luke Williams <shmookey@shmookey.net>

Distributed under the MIT license, see LICENSE file for details.
'''

class DocumentNotFound (Exception):
    pass

class TransactionError (Exception):
    pass

class TypeMismatch (Exception):
    pass

class SchemaError (Exception):
    pass

class ValidationError (Exception):
    pass

class ValidationTypeError (ValidationError):
    def __init__ (self, expected, got):
        self.expected = expected
        self.got = got
        self.message = 'Expected %s, got %s' % (expected,got)
        print self.message

class ValidationKeyError (ValidationError):
    def __init__ (self, key):
        self.key = key
        self.message = 'Unexpected key: %s' % key
        print self.message

class SchemaUnknownType (Exception):
    def __init__ (self, schema):
        self.schema = schema
        self.message = 'Cannot determine type in schema %s' % schema
        print self.message

class ValidationListError (ValidationError):
    pass

class SchemaTypeError (Exception):
    def __init__ (self, schema, details):
        self.schema = schema
        self.message = 'Type error in schema %s. Details: %s' % (schema, details)
        print self.message
        

