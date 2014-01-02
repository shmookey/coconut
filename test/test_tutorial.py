#!/usr/bin/python
'''test_tutorials.py -- Test the Coconut tutorial programs.'''

import unittest

from pymongo import MongoClient
from bson.objectid import ObjectId

import coconut.container
coconut.container.Document.__db__ = MongoClient()['test']

class TestExamples (unittest.TestCase):
    def test_getting_started (self):
        # Declare a Document type and annotate it with a schema
        class Person (coconut.container.Document):
            __schema__ = {
                'name':    { str: any, 'index':'unique' },
                'age':     { int: any },
                'referer': { id: 'Person' },
            }
        
        # Create, update and save some instances
        john = Person(name='Jonno',age=32)
        john.name = 'Jonathan'  # Use attribute-style access
        john['name'] = 'John'   # Or dict-style access
        john.save()
        fred = Person({'name':'Fred','age':29,'referer':john})
        fred.save()
        
        # Find records
        john2 = Person[john.id]                           # By array-style access
        fred2 = Person.find({'_id':ObjectId(fred.id)})[0] # By MongoDB query
        john3 = fred2.referer()                           # By link dereferencing
        
        # View history
        for i in range(5):
            john.age += 1
            john.save()
        history = john.history('age')
        for i,age in enumerate(history):
            self.assertEquals(37-i,age)
 

    def test_example_1 (self):
        class MyDocument (coconut.container.Document):
            pass
        
        doc = MyDocument()
        doc['foo'] = 'bar'
        doc.save()
        
        doc2 = MyDocument[doc.id]
        self.assertEquals(doc2['foo'],'bar')



