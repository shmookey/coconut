#!/usr/bin/python2.7

import coconut.container
from coconut.db import get_db
from coconut.error import *

import unittest

class TestDBSchema (unittest.TestCase):
    '''Test schema construction.'''

    def tearDown(self):
        db = get_db()
        db.TestDocumentSchemaKey.remove()
        db.TestDocumentSchemaType.remove()

    def test_invalid_key_raises_exception (self):
        '''A schema with an unrecognised key raises a SchemaError.'''

        class TestDocumentSchemaKey (coconut.container.Document):
            __schema__ = { 'attr': { str: any, 'not_a_real_key':'error' } }

        def f():
            doc1 = TestDocumentSchemaKey()

        self.assertRaises(SchemaError,f)

    def test_missing_datatype_raises_exception (self):
        '''A schema missing a datatype raises a SchemaError.'''

        class TestDocumentSchemaType (coconut.container.Document):
            __schema__ = { 'attr': { 'index':'unique' } }

        def f():
            doc1 = TestDocumentSchemaType()

        self.assertRaises(SchemaError,f)

if __name__ == '__main__':
    unittest.main()
