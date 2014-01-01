#!/usr/bin/python2.7

import coconut.container
from coconut.db import get_db
from coconut.error import ValidationTypeError, ValidationKeyError

import unittest

class TestDBPrimitives (unittest.TestCase):
    '''Test primitive types.'''

    def tearDown(self):
        db = get_db()
        db.TestDocument.remove()

    def test_assign_string_attr_to_string_attr (self):
        '''A string attribute can be assigned the value of another string attribute.'''

        class TestDocument (coconut.container.Document):
            __schema__ = { 'attr': { str: any } }

        doc1 = TestDocument({'attr':'foo'})
        doc2 = TestDocument({'attr':'bar'})
        doc1.attr = doc2.attr
        self.assertEquals(doc1.attr,doc2.attr)
        self.assertEquals(doc1.attr,'bar')

    def test_increment_int (self):
        '''An integer attribute can be incremented with the += operator.'''

        class TestDocument (coconut.container.Document):
            __schema__ = { 'attr': { int: any } }

        doc = TestDocument({'attr':0})
        doc.attr += 1
        self.assertEquals(doc.attr,1)

if __name__ == '__main__':
    unittest.main()
