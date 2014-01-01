#!/usr/bin/python2.7

import coconut.container
import coconut.element
import coconut.schema
from coconut.error import ValidationTypeError, ValidationKeyError

import unittest

class TestDocument (coconut.container.Document):
    __schema__ = {
        'attr_str':          { str:   any},
        'attr_int':          { int:   any },
        'attr_float':        { float: any },
        'attr_dict':         { dict:  any },
        'attr_static_link':  { id:    'TestDocument' },
        'attr_dynamic_link': { id:    any },
        'attr_list':         { list:  any },
        'attr_typeddict':    { dict:  {
            'key':             { str: any }, } },
        'attr_typedlist':    { list:
                             [ { str:   any },
                               { float: any }, ] },
        'attr_rangelist':    { list: 
                             [ { str:   any } ],
                               range: all },
        'attr_str_default':  { str:   any, 'default': 'value' },
        'attr_list_default': { list:  any, 'default': [] },
        'list_of_links':     { list: 
                             [ { id: 'AnotherTestDocument' } ],
                               range: all,
                               'default': [] },
        'dict_list_links':   { list: [ 
                               { dict: { 
                                   'key': {id: 'AnotherTestDocument'} } } ],
                               range: all,
                               'default': [] },
    }

class AnotherTestDocument (coconut.container.Document):
    __schema__ = {
        'name': { str: any },
    }
        

class TestSchema (unittest.TestCase):
    '''Test suite for schema.py

    Tests still to be written:
     - Traverse option enables/disables value conversion
     - List range: all option causes all items to be validated against first schema entry
     - List range: all option raises error if list schema has more than one entry
     - Dict raises exception on attempt to set nonexistent key with non-any schema
    '''
    def setUp (self):
        self.source_data = {
            'attr_str': 'Test string',
            'attr_int': 42,
            'attr_float': 3.14159,
            'attr_dict': {
                'subattr_str': 'Another Test String',
            },
        }
        self.other_data = {
            'name': 'Linked Document',
        }

    def test_import (self):
        instance = TestDocument (self.source_data)
        self.assertIsInstance (instance, TestDocument)

    def test_default_string (self):
        '''An unset string key gets assigned a default value.'''
        instance = TestDocument (self.source_data)
        self.assertEquals(instance.attr_str_default, 'value')

    def test_dict_set_invalid_key (self):
        '''Setting an invalid key on a dict raises a ValidationKeyError.'''
        instance = TestDocument (self.source_data)
        def f():
            instance['somekey'] = 'blah'
        self.assertRaises(ValidationKeyError, f)
        
    def test_dict_set_invalid_value (self):
        '''Setting an invalid value on a dict raises a ValidationTypeError.'''
        instance = TestDocument (self.source_data)
        instance.attr_typeddict = {}
        def f():
            instance.attr_typeddict['key'] = 42
        self.assertRaises(ValidationTypeError, f)
        
    def test_export (self):
        instance = TestDocument (self.source_data)
        self.assertIsInstance (instance, TestDocument)
        export = coconut.schema.Schema.export_element(instance)
        self.assertEqual (export['attr_str'], self.source_data['attr_str'])
        self.assertEqual (export['attr_int'], self.source_data['attr_int'])
        self.assertEqual (export['attr_float'], self.source_data['attr_float'])
        
    def test_dict_access (self):
        instance = TestDocument (self.source_data)
        for key in self.source_data:
            if not isinstance(instance[key],dict):
                self.assertEqual(instance[key], self.source_data[key])
        self.assertEqual(instance['attr_dict']['subattr_str'], self.source_data['attr_dict']['subattr_str'])

    def test_attribute_access (self):
        instance = TestDocument (self.source_data)
        self.assertEqual (instance.attr_str, self.source_data['attr_str'])
        self.assertEqual (instance.attr_int, self.source_data['attr_int'])
        self.assertEqual (instance.attr_float, self.source_data['attr_float'])

    def test_save_and_load (self):
        instance2 = TestDocument (self.source_data)
        instance2.save()
        instance = TestDocument[instance2.id]
        self.assertEqual (instance.attr_str, self.source_data['attr_str'])
        self.assertEqual (instance.attr_int, self.source_data['attr_int'])
        self.assertEqual (instance.attr_float, self.source_data['attr_float'])
        self.assertEqual (instance.attr_dict['subattr_str'], self.source_data['attr_dict']['subattr_str'])

    def test_links (self):
        dynamic_link_instance = AnotherTestDocument({'name':'Dynamic Link Target'})
        dynamic_link_instance.save()

        instance1 = TestDocument (self.source_data)
        instance1.attr_str = 'Linked Document'
        instance1.attr_dynamic_link = dynamic_link_instance
        instance1.save()

        instance2 = TestDocument(self.source_data)
        instance2.attr_static_link = instance1
        self.assertIsInstance (instance2.attr_static_link,coconut.element.Link)
        instance2.save()

        instance3 = TestDocument[instance2.id]

        link = instance3.attr_static_link
        target = link()
        self.assertEqual (link.targetid,instance1.id)
        self.assertEqual (target.attr_str,'Linked Document')

        instance4 = target.attr_dynamic_link()

        self.assertEqual (dynamic_link_instance.name, instance4.name)

if __name__ == '__main__':
    unittest.main()
