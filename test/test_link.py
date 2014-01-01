#!/usr/bin/python2.7

import unittest

from pymongo import MongoClient

import coconut.container
from coconut.error import UniqueIndexViolation

class TestDBLinks (unittest.TestCase):
    '''Test the Link type.'''

    def setUp (self):
        self.db = coconut.container.Document.__db__ = MongoClient().coconut_test

    def tearDown(self):
        self.db.TestDocumentLink.remove()

    def test_export_link_becomes_objectid (self):
        '''A schema may include the mapping index:True.'''

        class TestDocumentIndex (coconut.container.Document):
            __schema__ = { 'attr': { str: any, 'index':True } }

        doc1 = TestDocumentIndex({'attr':'foo'})

if __name__ == '__main__':
    unittest.main()

