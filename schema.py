''' schema.py -- Python object schemas for Coconut
Author: Luke Williams <shmookey@shmookey.net>

Distributed under the MIT license, see LICENSE file for details.
'''

from coconut.error import *
from coconut.primitive import Element, Int, Str, Float
import coconut.container

from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.dbref import DBRef

import copy, inspect, time

class Schema (object):
    '''Base class for field types representing containers.

    A schema is a dict that describes the structure of an object. 
    
    Schemas for reference types contain an *id* key which maps to either the
    class of the Document type referenced by the field, to the class name, or
    to the *any* keyword, if the field may reference different Document types.

    Schemas for primitive objects contain a *type* key that maps to either the
    type or the type name. Setting *type* to *list* or *dict* allows these
    collection types to be added without further processing or validation by
    the schema.

    Schemas for lists contain a *list* key which maps to a list of schemas
    for the objects expected in the list. List schemas may also have a *range*
    key, which provides for lists of unknown length or contents. A *range*
    value of *all* applies the first schema in the list to all elements in the
    target list. A value of *any* tries each of the schemas in the list for
    each value in the target list and applies the first that validates.

    Schemas for dicts contain a *dict* key which contains keys corresponding to
    keys in the source document, each mapping to a schema. It may also contain
    a *filter* key, which causes keys in the source document that do not occur
    in the schema to be skipped if set to True. The default value is False, so
    keys with no corresponding schema are copied without further validation.
 
    Example schema for a Map (dict type) field containing user information:
    {
        'username': {type: str},
        'group': {id: 'Group'},
        'friends': {
            list: [{id: 'User'}],
            range: all
        },
        'likes': {
            list: [{id: any}],
            range: all
        }
    }
    '''

    def validate_schema (self, structure):
        pass

    @classmethod
    def get_type (cls, schema):
        if schema == any: return any
        for t in [list,dict,id,str,int,bool,float,any]:
            if t in schema: return t
        raise SchemaUnknownType (schema)

    @classmethod
    def import_document (self, source, document):
        '''Generate a Document from its database representation.'''
        document.__unsaved__ = Schema.import_element (source, {dict:document.__schema__}, document)

    @classmethod
    def import_element (cls, source, schema, parent):
        '''Generate an Element from source data according to a schema.'''
        # TODO: Non-nullable fields
        Schema.validate_schema(schema)
        if source == None: return source

        element = None
        expected = Schema.get_type(schema)
        element_type = type(source)

        # Convert unicode to strings before letting an 'any' schema set the expected type
        if element_type == unicode:
            element_type = str
            source = source.encode('utf-8')
 
        if expected == any:
            # If we're expecting anything, we're expecting what we get
            value_schema = any
            if issubclass(element_type, DBRef) or issubclass(element_type, ObjectId):
                expected = id
            else:
                expected = element_type 
        else:
            value_schema = schema[expected]

        if expected == id:
            element = coconut.element.Link (source, schema=schema)
            return element

        if not issubclass(element_type, expected) and not (expected == float and issubclass(element_type,int)):
            raise ValidationTypeError(expected,element_type)

        # TODO: Validate primitives
        if issubclass(element_type,str): element = Str(source)
        elif issubclass(element_type,int): element = Int(source)
        elif issubclass(element_type,float): element = Float(source)
        elif issubclass(element_type,bool): element = source

        elif element_type == list:
            # TODO: Implement 'any'
            element = coconut.container.List(parent=parent,schema=schema)
            for i, item in enumerate(source):
                element.append(item)

        elif element_type == dict:
            element = coconut.container.Dict(parent=parent,schema=schema)
            for key, item in source.items():
                element[key] = item
            # Check for missing keys with default values
            if isinstance(schema,dict) and dict in schema and isinstance(schema[dict],dict):
                for key, item_schema in schema[dict].items():
                    if not key in element:
                        if isinstance(item_schema,dict) and 'default' in item_schema:
                            element[key] = copy.deepcopy(item_schema['default'])
                        else:
                            element[key] = None
        else:
            raise ValidationTypeError ('type compatible with schema %s' % schema, element_type)

        return element

    @classmethod
    def export (cls, document):
        '''Generate a database-friendly document from a Document object.'''
        return Schema.export_element (document, document.__schema__)

    @classmethod
    def export_element (cls, source, schema=None):
        '''Generate a database element from an Element object.'''
        # TODO: Non-nullable fields
        if source == None: return source
        if not schema:
            if not isinstance(source,coconut.container.MutableElement):
                raise ValueError ('Source must be of MutableElement type if no schema specified.')
            schema = source.__schema__
        Schema.validate_schema(schema)
        element = None
        expected = Schema.get_type(schema)
        element_type = type(source)
        
        if expected == any:
            # If we're expecting anything, we're expecting what we get
            expected = element_type
            value_schema = any
        elif expected == id:
            # If we're expecting an id, we're really expecting a Link
            expected = coconut.element.Link
            value_schema = schema[id]
        else:
            value_schema = schema[expected]

        if not issubclass(element_type,Element):
            raise ValidationTypeError(Element,element_type)

        if not issubclass(element_type, expected) and not (expected == float and issubclass(element_type,int)):
            raise ValidationTypeError(expected,element_type)

        if filter(lambda t: isinstance(source,t),[str,int,float,bool]):
            # Don't do anything for primitives
            element = source
        elif isinstance(source, coconut.element.Link):
            element = source.format_db()
        elif isinstance(source, list):
            element = []
            for i, item in enumerate(source):
                item_schema = Schema.get_list_index_schema(i,schema)
                new_item = Schema.export_element(item,item_schema)
                element.append(new_item)

        elif isinstance(source,dict):
            element = {}
            for key, item in source.items():
                if value_schema == any:
                    new_item = Schema.export_element(item,value_schema)
                elif not key in value_schema:
                    raise ValidationKeyError (key)
                else:
                    item_schema = value_schema[key]
                    new_item = Schema.export_element(item,item_schema)
                element[key] = new_item
        
        else:
            raise ValidationTypeError ([id,str,int,float,bool,list,dict,any], element_type)

        return element

    @classmethod
    def get_list_index_schema (cls, idx, schema):
        if schema == any: return any
        if any in schema: return any
        if not list in schema: raise SchemaError()
        item_schemas = schema[list]
        schema_range = schema.get(range,None)
        if item_schemas == any:
            if schema_range == all: return any
            else: raise ValidationListError()
        elif not isinstance(item_schemas,list):
            raise SchemaError()
        if idx < len(item_schemas):
            return item_schemas[idx]
        if schema_range == all:
            return item_schemas[0]
        raise ValidationListError()

    @classmethod
    def validate_schema (cls, schema):
        '''Raise an exception if a schema has missing or unsupported keys.'''

        if schema == any: return
        t = cls.get_type (schema) # Checks for data type
        for (key,val) in schema.items():
            if key == t: continue
            if key in ['default','index']: continue
            if t == list and key in [range]: continue
            if t in [list,dict] and key in ['traverse']: continue
            raise SchemaUnknownKey(key,schema)
        
