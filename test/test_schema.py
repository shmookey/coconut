#!/usr/bin/python2.7

import unittest

from pymongo import MongoClient

import coconut.container
from coconut.error import *

class TestDBSchema (unittest.TestCase):
    '''Test schema construction.'''

    def setUp (self):
        self.db = coconut.container.Document.__db__ = MongoClient().coconut_test

    def tearDown(self):
        self.db.TestDocumentSchemaKey.remove()
        self.db.TestDocumentSchemaType.remove()

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

    def test_any_schema_set_arbitrary_keys (self):
        '''Arbitrary key values can be set on a Document with the any schema.'''

        class TestDocumentSchemaType (coconut.container.Document):
            # Use the default schema
            pass

        doc = TestDocumentSchemaType()
        doc['foo'] = 'bar'
        self.assertEquals(doc['foo'],'bar')

    def test_any_schema_load_arbitrary_keys (self):
        '''Arbitrary key values can be set on a Document with the any schema.'''

        class TestDocumentSchemaType (coconut.container.Document):
            # Use the default schema
            pass

        doc = TestDocumentSchemaType({'foo':'bar'})
        self.assertEquals(doc['foo'],'bar')

    def test_any_schema_save_arbitrary_keys (self):
        '''Arbitrary key values can be saved on a Document with the any schema.'''

        class TestDocumentSchemaType (coconut.container.Document):
            # Use the default schema
            pass

        doc = TestDocumentSchemaType()
        doc['foo'] = 'bar'
        self.assertEquals(doc['foo'],'bar')
        doc.save()
        

    def test_any_schema_load_saved_arbitrary_keys (self):
        '''Arbitrary key values can be saved on a Document with the any schema.'''

        class TestDocumentSchemaType (coconut.container.Document):
            # Use the default schema
            pass

        doc = TestDocumentSchemaType()
        doc['foo'] = 'bar'
        doc.save()
        doc2 = TestDocumentSchemaType[doc.id]
        self.assertEquals(doc2['foo'],'bar')
        

# TODO: attribute access for documents with the any schema        
#    def test_any_schema_arbitrary_attribute_access (self):
#        '''Arbitrary key values can be set on a Document with the any schema.'''
#
#        class TestDocumentSchemaType (coconut.container.Document):
#            # Use the default schema
#            pass
#
#        doc = TestDocumentSchemaType()
#        doc.foo = 'bar'
#        self.assertEquals(doc['foo'],'bar')

if __name__ == '__main__':
    unittest.main()
