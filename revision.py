''' revision.py -- Revision control for Coconut documents
Author: Luke Williams <shmookey@shmookey.net>

Distributed under the MIT license, see LICENSE file for details.
'''

import coconut.container

import pymongo

class History (object):
    def __init__ (self, document, field):
        self.document = document
        self.field = field
        self.current = None
        if field: self.path = field.split('.')
        else: self.path = None

    def __iter__ (self):
        return self

    def next (self):
        query = {
            'item.$id': self.document.id,
        }
        if self.current:
            query['date'] = {'$lt':self.current.date}
        if self.field: query['changes.set.%s' % self.field] = {'$exists':True}
        revisions = coconut.revision.Revision.find(query, sort=('date',pymongo.DESCENDING), limit=1)
        if not revisions:
            raise StopIteration()
        self.current = revisions[0]
        component = self.current.changes['set']
        if not self.path: return component
        for term in self.path:
            component = component[term]
        return component

class Revision (coconut.container.Document):
    '''A change event to a document.'''

    __schema__ = {dict:{
      'item':    { id:    any },
      'changes': { dict:  any, 'traverse':False },
      'date':    { float: any, 'index':True },
    }}


