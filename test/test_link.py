#!/usr/bin/python2.7

import coconut.container
from coconut.db import get_db
from coconut.error import UniqueIndexViolation

import unittest

class TestDBLinks (unittest.TestCase):
    '''Test the Link type.'''

    def setUp (self):
        self.db = get_db()

    def tearDown(self):
        self.db.TestDocumentLink.remove()

    def test_export_link_becomes_objectid (self):
        '''A schema may include the mapping index:True.'''

        class TestDocumentIndex (coconut.container.Document):
            __schema__ = { 'attr': { str: any, 'index':True } }

        doc1 = TestDocumentIndex({'attr':'foo'})

if __name__ == '__main__':
    unittest.main()

