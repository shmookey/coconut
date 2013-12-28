#!/usr/bin/python2.7

from coconut.container import Document
from coconut.schema import Schema
from coconut.element import Link
from coconut.db import get_db
from coconut.error import ValidationTypeError, ValidationKeyError

import unittest

class AnotherTestDocument (Document):
    __schema__ = {
        'name': { str: any },
    }
        

class TestDBLists (unittest.TestCase):
    '''Test DB List types.'''
    def tearDown(self):
        db = get_db()
        db.TestDocument_List.remove()
        db.AnotherTestDocument.remove()

    def gen_doc (self, save=False):
        '''Return a new unsaved AnotherTestDocument instance.'''
        doc = AnotherTestDocument({'name':'Some Document'})
        if save: doc.save()
        return doc

    def test_default_list_on_import (self):
        '''The 'default' schema option assigns a given value to an unspecified list in a document being imported.'''

        class TestDocument_List (Document):
            __schema__ = { 'defaulted': { list: any, 'default': [] } }

        instance = TestDocument_List ()
        self.assertIsInstance(instance.defaulted, list)
        self.assertEquals(len(instance.defaulted), 0)

    def test_append_invalid_value_raises_keyerror (self):
        '''Appending an invalid value on an empty fixed-schema list raises a ValidationKeyError.'''
        
        class TestDocument_List (Document):
            __schema__ = { 'typed': {
              list: [ { str: any }, { float: any } ],
              'default': [], },
            }

        instance = TestDocument_List ()
        instance.typed.append ('valid value')
        def f():
            instance.typed.append ('invalid value')
        self.assertRaises(ValidationTypeError, f)
        
    def test_append_value_typed_list (self):
        '''Appending a valid value to a typed list makes that value available.'''
        
        class TestDocument_List (Document):
            __schema__ = { 'typed': {
              list: [ { str: any }, { float: any } ],
              'default': [], },
            }

        instance = TestDocument_List ()
        instance.typed.append ('valid value')
        self.assertEquals('valid value',instance.typed[0])

    def test_append_document_with_schema (self):
        '''Appending an Document on a schema-controlled list creates a new Link.'''

        class TestDocument_List (Document):
            __schema__ = { 'of_links': {
              list: [ { id: 'AnotherTestDocument' } ],
              range: all,
              'default': [] },
            }

        instance = TestDocument_List ()
        linked = self.gen_doc(True)
        instance.of_links.append (linked)
        self.assertEquals(instance.of_links[0].targetid, linked.id)
        
    def test_dict_list_append_document (self):
        '''Appending an dict containing a key mapped to a Document creates a new Link.'''
        
        class TestDocument_List (Document):
            __schema__= {
              'dict_links': {
                list: [ { dict: { 'key': { id: 'AnotherTestDocument' } } } ],
                range: all,
                'default': []
              },
          }
        instance = TestDocument_List ()
        linked = self.gen_doc(True)
        instance.dict_links.append ({'key':linked})
        self.assertEquals(len(instance.dict_links), 1)
        self.assertIn('key', instance.dict_links[0])
        self.assertEquals(instance.dict_links[0]['key'].targetid, linked.id)
        
    def test_set_invalid_value_raises_typerror (self):
        '''Setting an invalid value on a schema-managed list raises a ValidationTypeError.'''

        class TestDocument_List (Document):
            __schema__ = { 'typed': {
              list: [ { str: any }, { float: any } ],
              'default': [] },
            }

        instance = TestDocument_List ()
        instance.typed.append ('valid value')
        instance.typed.append (42.0)
        def f():
            instance.typed[1] = 'invalid value'
        self.assertRaises(ValidationTypeError, f)
        self.assertEquals(instance.typed[1], 42.0)
        
    def test_import_ranged_any_any_list (self):
        '''Arbitrary source list values with the any:any schema are available after import.'''

        class TestDocument_List (Document):
            __schema__ = { 'ranged': {
              list: [ { any: any } ],
              range: all }
            }

        data = {'ranged':['something',5,2.71]}
        instance = TestDocument_List (data)
        for i,item in enumerate(data['ranged']):
            self.assertEquals (instance.ranged[i], item)
        
    def test_import_ranged_str_any_list (self):
        '''Arbitrary string values with the str:any schema are available after import.'''

        class TestDocument_List (Document):
            __schema__ = { 'ranged': {
              list: [ { str: any } ],
              range: all }
            }

        data = {'ranged':['something','something else']}
        instance = TestDocument_List (data)
        for i,item in enumerate(data['ranged']):
            self.assertEquals (instance.ranged[i], item)
        
    def test_import_list_any_list (self):
        '''Arbitrary values on a list:any schema are available after import.'''

        class TestDocument_List (Document):
            __schema__ = { 'anylist': { list: any, range: all } }

        data = {'anylist':['something','something else']}
        instance = TestDocument_List (data)
        for i,item in enumerate(data['anylist']):
            self.assertEquals (instance.anylist[i], item)
        
    def test_import_any_list (self):
        '''Setting an 'any' key to a list retains the values.'''

        class TestDocument_List (Document):
            __schema__ = { 'anylist': any }

        data = {'anylist':['something','something else']}
        instance = TestDocument_List (data)
        for i,item in enumerate(data['anylist']):
            self.assertEquals (instance.anylist[i], item)
        
        
    def test_list_save_load (self):
        '''Save and load a list.'''

        class TestDocument_List (Document):
            __schema__ = { 'typed': {
              list: [ { str: any }, { int: any }, { float: any } ],
              'default': [] }
            }


        data = {'typed':['something',5,2.71]}
        instance = TestDocument_List (data)
        instance.save()
        loaded = TestDocument_List[instance.id]
        for i,item in enumerate(data['typed']):
            self.assertEquals (loaded.typed[i], item)

if __name__ == '__main__':
    unittest.main()
