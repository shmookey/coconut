#!/usr/bin/python
'''test_tutorials.py -- Test the Coconut tutorial programs.'''

import unittest

from pymongo import MongoClient

import coconut.container
coconut.container.Document.__db__ = MongoClient()['test']

class TestExamples (unittest.TestCase):
    def test_example_1 (self):
        class MyDocument (coconut.container.Document):
            pass
        
        doc = MyDocument()
        doc['foo'] = 'bar'
        doc.save()
        
        doc2 = MyDocument[doc.id]
        self.assertEquals(doc2['foo'],'bar')



