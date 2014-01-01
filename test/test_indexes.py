#!/usr/bin/python2.7

import coconut.container
from coconut.db import get_db
from coconut.error import UniqueIndexViolation

import unittest

class TestDBIndexes (unittest.TestCase):
    '''Test primitive types.'''

    def setUp (self):
        self.db = get_db()

    def tearDown(self):
        self.db.TestDocumentIndex.drop_indexes()
        self.db.TestDocumentIndex.remove()

    def test_schema_index_true (self):
        '''A schema may include the mapping index:True.'''

        class TestDocumentIndex (coconut.container.Document):
            __schema__ = { 'attr': { str: any, 'index':True } }

        doc1 = TestDocumentIndex({'attr':'foo'})

    def test_schema_index_unique (self):
        '''A schema may include the mapping 'index':'unique'.'''

        class TestDocumentIndex (coconut.container.Document):
            __schema__ = { 'attr': { str: any, 'index':'unique' } }

        doc1 = TestDocumentIndex({'attr':'foo'})

    def test_ensure_index_simple (self):
        '''ensure_indexes on a Document with an simple indexed schema creates one single-key MongoDB index.'''

        class TestDocumentIndex (coconut.container.Document):
            __schema__ = { 'attr': { str: any, 'index':True } }

        self.db.TestDocumentIndex.drop_indexes()
        TestDocumentIndex.ensure_indexes()
        indexes = self.db.TestDocumentIndex.index_information()

        self.assertEquals(len(indexes),2) # Includes default _id index
        for (idx,info) in indexes.items():
            if idx == '_id_': continue
            self.assertEquals(idx[:4],'attr')
            self.assertEquals(info['key'][0][0],'attr')

    def test_unique_index_enforced (self):
        '''Violating a unique index raises an UniqueIndexViolation upon saving.'''

        class TestDocumentIndex (coconut.container.Document):
            __schema__ = { 'attr': { str: any, 'index':'unique' } }

        TestDocumentIndex.ensure_indexes()
        doc1 = TestDocumentIndex({'attr':'foo'})
        doc2 = TestDocumentIndex({'attr':'foo'})
        doc1.save()

        def f():
            doc2.save()

        self.assertRaises(UniqueIndexViolation,f)

if __name__ == '__main__':
    unittest.main()

