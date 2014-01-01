#!/usr/bin/python2.7

import time, unittest

from pymongo import MongoClient
from bson.objectid import ObjectId

import coconut.container
import coconut.revision

class TestDBRevision (unittest.TestCase):
    '''Test the revision control mechanism.'''

    def setUp (self):
        self.db = coconut.container.Document.__db__ = MongoClient().coconut_test

    def tearDown(self):
        self.db.TestDocumentRevision.remove()
        #self.db.Revision.remove({'item.$ref':'TestDocumentRevision'})

    def test_create_initial_revision (self):
        '''Inserting a new Document creates an initial Revision.'''

        class TestDocumentRevision (coconut.container.Document):
            __schema__ = { 'attr': { str: any } }

        doc1 = TestDocumentRevision({'attr':'foo'})
        doc1.save()

        revisions = coconut.revision.Revision.find({'item.$id':doc1.id})
        self.assertEquals (len(revisions), 1)
        r = revisions[0]
        self.assertIn ('attr', r.changes['set'])
        self.assertEquals (r.changes['set']['attr'], 'foo')

    def test_minimal_shallow_differential (self):
        '''Shallow updates create record a minimal differential.'''

        class TestDocumentRevision (coconut.container.Document):
            __schema__ = { 'foo': { str: any }, 'bar': { str: any } }

        doc = TestDocumentRevision({'foo':'something'})
        doc.save()

        revision = coconut.revision.Revision.find({'item.$id':doc.id})[0]
        self.assertIn ('foo', revision.changes['set'])
        # For now we expect all fields in the schema to be recorded the first time, even if not set
        self.assertIn ('bar', revision.changes['set'])

        doc.bar = 'value'
        doc.save()

        revisions = coconut.revision.Revision.find({'item.$id':doc.id,'_id':{'$ne':ObjectId(revision.id)}})
        self.assertEquals (len(revisions),1)
        r2 = revisions[0]
        self.assertNotIn ('foo', r2.changes['set'])
        self.assertIn ('bar', r2.changes['set'])

    def test_minimal_subkey_differential (self):
        '''Subkey updates create record a minimal differential.'''

        class TestDocumentRevision (coconut.container.Document):
            __schema__ = {
                'thang': { dict: { 
                    'thing': { str: any }, 
                    'thong': { str: any } 
                } }
            }

        doc = TestDocumentRevision({'thang':{'thing':'foo','thong':'bar'}})
        doc.save()
        r = coconut.revision.Revision.find({'item.$id':doc.id})[0]
        doc.thang['thing'] = 'different'
        doc.save()
        r2 = coconut.revision.Revision.find({'item.$id':doc.id,'_id':{'$ne':ObjectId(r.id)}})[0]
        self.assertIn ('thing',r2.changes['set']['thang'])
        self.assertNotIn ('thong',r2.changes['set']['thang'])

    def test_history_document (self):
        '''Iterate over a document's revision history.'''

        class TestDocumentRevision (coconut.container.Document):
            __schema__ = { 'foo': { int: any } }

        doc = TestDocumentRevision()
        for i in range(5):
            doc.foo = i
            doc.save()

        history = doc.history()
        for j, val in enumerate(history):
            self.assertEquals(val['foo'],4-j)
        self.assertEquals(j,j)

    def test_history_shallow_key (self):
        '''Iterate over a document key's revision history.'''

        class TestDocumentRevision (coconut.container.Document):
            __schema__ = { 'foo': { int: any }, 'bar': { int: any } }

        doc = TestDocumentRevision()
        for i in range(5):
            doc.foo = i
            doc.save()
            doc.bar = i+1
            doc.save()

        history = doc.history('foo')
        for j, val in enumerate(history):
            self.assertEquals(val,4-j)
        self.assertEquals(j,4)


    def test_history_subkey (self):
        '''Iterate over a document key's revision history.'''

        class TestDocumentRevision (coconut.container.Document):
            __schema__ = {
                'thang': { dict: { 
                    'thing': { int: any }, 
                    'thong': { int: any } 
                } }
            }

        doc = TestDocumentRevision({'thang':{'thing':0,'thong':0}})
        doc.save()

        for i in range(5):
            doc.thang['thing'] = i
            doc.save()
            doc.thang['thong'] = i*2
            doc.save()

        history = doc.history('thang.thing')
        for j, val in enumerate(history):
            self.assertEquals(val,4-j)
        self.assertEquals(j,4)

if __name__ == '__main__':
    unittest.main()

