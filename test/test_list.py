#!/usr/bin/python2.7

import unittest

from pymongo import MongoClient

import coconut.container
from coconut.error import ValidationTypeError, ValidationKeyError

class AnotherTestDocument (coconut.container.Document):
    __schema__ = {
        'name': { str: any },
    }
        

class TestDBLists (unittest.TestCase):
    '''Test DB List types.'''

    def setUp (self):
        db = self.db = coconut.container.Document.__db__ = MongoClient().coconut_test

    def tearDown(self):
        db = self.db
        db.TestDocument_List.remove()
        db.AnotherTestDocument.remove()

    def gen_doc (self, save=False):
        '''Return a new unsaved AnotherTestDocument instance.'''
        doc = AnotherTestDocument({'name':'Some Document'})
        if save: doc.save()
        return doc

    def test_default_list_on_import (self):
        '''The 'default' schema option assigns a given value to an unspecified list in a document being imported.'''

        class TestDocument_List (coconut.container.Document):
            __schema__ = { 'defaulted': { list: any, 'default': [] } }

        instance = TestDocument_List ()
        self.assertIsInstance(instance.defaulted, list)
        self.assertEquals(len(instance.defaulted), 0)

    def test_append_invalid_value_raises_keyerror (self):
        '''Appending an invalid value on an empty fixed-schema list raises a ValidationKeyError.'''
        
        class TestDocument_List (coconut.container.Document):
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
        
        class TestDocument_List (coconut.container.Document):
            __schema__ = { 'typed': {
              list: [ { str: any }, { float: any } ],
              'default': [], },
            }

        instance = TestDocument_List ()
        instance.typed.append ('valid value')
        self.assertEquals('valid value',instance.typed[0])

    def test_append_document_with_schema (self):
        '''Appending an Document on a schema-controlled list creates a new Link.'''

        class TestDocument_List (coconut.container.Document):
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
        
        class TestDocument_List (coconut.container.Document):
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

        class TestDocument_List (coconut.container.Document):
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

        class TestDocument_List (coconut.container.Document):
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

        class TestDocument_List (coconut.container.Document):
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

        class TestDocument_List (coconut.container.Document):
            __schema__ = { 'anylist': { list: any, range: all } }

        data = {'anylist':['something','something else']}
        instance = TestDocument_List (data)
        for i,item in enumerate(data['anylist']):
            self.assertEquals (instance.anylist[i], item)
        
    def test_import_any_list (self):
        '''Setting an 'any' key to a list retains the values.'''

        class TestDocument_List (coconut.container.Document):
            __schema__ = { 'anylist': any }

        data = {'anylist':['something','something else']}
        instance = TestDocument_List (data)
        for i,item in enumerate(data['anylist']):
            self.assertEquals (instance.anylist[i], item)
        
        
    def test_list_save_load (self):
        '''Save and load a list.'''

        class TestDocument_List (coconut.container.Document):
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

    def test_list_assign (self):
        '''Assign a list to a list field.'''

        class TestDocument_List (coconut.container.Document):
            __schema__ = { 'foo': {
              list: [ { str: any } ],
              range: all,
              'default': [] }
            }


        instance = TestDocument_List ()
        data = ['a','b','c']
        instance.foo = data
        instance.save()
        for i,item in enumerate(data):
            self.assertEquals(instance.foo[i], item)
        # Are the updated values available after loading?
        instance2 = TestDocument_List[instance.id]
        for i,item in enumerate(data):
            self.assertEquals(instance2.foo[i], item)
        

    def test_list_reassign (self):
        '''Reassign a list to a list field.'''

        class TestDocument_List (coconut.container.Document):
            __schema__ = { 'foo': {
              list: [ { str: any } ],
              range: all,
              'default': [] }
            }


        instance = TestDocument_List ()
        instance.foo = ['a','b','c']
        instance.save()
        data = ['d','e','f']
        instance.foo = data
        instance.save()
        for i,item in enumerate(data):
            self.assertEquals(instance.foo[i], item)
        # Are the updated values available after loading?
        instance2 = TestDocument_List[instance.id]
        for i,item in enumerate(data):
            self.assertEquals(instance2.foo[i], item)

    def test_list_reassign_different_length (self):
        '''Reassign a list of a different length to a list field.'''

        class TestDocument_List (coconut.container.Document):
            __schema__ = { 'foo': {
              list: [ { str: any } ],
              range: all,
              'default': [] }
            }


        instance = TestDocument_List ()
        instance.save()
        data = ['d','e','f','g']
        for item in data:
            instance.foo.append(item)
        instance.save()
        for i,item in enumerate(data):
            self.assertEquals(instance.foo[i], item)
        # Are the updated values available after loading?
        instance2 = TestDocument_List[instance.id]
        for i,item in enumerate(data):
            self.assertEquals(instance2.foo[i], item)

    def test_list_modify_one_leave_another (self):
        '''Modify one line but leave another unchanged.'''

        class TestDocument_List (coconut.container.Document):
            __schema__ = {
              'foo': {
                list: [ { str: any } ],
                range: all,
                'default': []
              }, 'bar': {
                list: [ { str: any } ],
                range: all,
                'default': []
              }
            }


        instance1 = TestDocument_List ()
        instance1.foo.append('hello')
        instance1.save()
        instance2 = TestDocument_List[instance1.id]
        sets, unsets = instance2.get_changes()
        print 'sets=%s' % sets
        instance2.bar.append('hi')
        instance2.save()
        self.assertEquals(instance2.foo[0], 'hello')
        self.assertEquals(instance2.bar[0], 'hi')
        
if __name__ == '__main__':
    unittest.main()
