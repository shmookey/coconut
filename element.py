''' element.py -- Basic Element types for Coconut.
Author: Luke Williams <shmookey@shmookey.net>

Distributed under the MIT license, see LICENSE file for details.
'''

from coconut.error import *
from coconut.db import get_db, SerialisableDBRef, SerialisableObjectId
from coconut.primitive import Element
import coconut.container
import coconut.schema

from bson.objectid import ObjectId
from bson.dbref import DBRef

import copy, inspect, json, time

def to_json (obj):
    return JSONElementEncoder().encode (obj)

class JSONElementEncoder (json.JSONEncoder):
    def default (self, o):
        if isinstance(o,coconut.container.MutableElement):
            return Schema.export_element(o)
        try:
            return o.__json__()
        except:
            pass
        return json.JSONEncoder.default(self, o)

#
# Reference Types
#

class Link (Element):
    '''Reference type for Documents.

    Instances can be called like functions to deference the link and return the
    referenced Document.

    Instance variables
     document -- The referenced Document object.
     objectid -- A PyMongo ObjectId referencing the object in a collection.
     id -- A string representation of the ObjectId parameter.
     doctype -- The class object of the Document's containing collection.
     doctype_name -- The name of the collection class.
    '''

    def __init__ (self, target=None, schema=None):
        '''Create a new link.

        Raises a TypeError if a collection is specified and the document target
        type does not match.
        
        A wide range of tagets representing Documents and references are
        supported.
        
        If the provided argument is a Document, Link, or Reference then all of
        the Link's attributes are set to match the argument.
        
        If the argument is an ObjectId or string, the id and objectid instance
        variables are set but the collection and collection_name variables are
        left unchanged. The document variable is set to None. Note that this
        operation can create an invalid reference if the referenced object
        belongs to a different collection. So... don't do that.
        
        If the argument is a list or a tuple, the first element can be either a
        Document subclass or a string and is used to set collection and
        collection_name, and the second element can be either a Document, Link,
        Reference, ObjectId or string and is used to set the remaining
        variables as if it were provided as the sole argument.
        
        If the argument is a dict, the keys 'collection' and 'ref' are used to
        form a tuple (collection,document) which is processed in the same
        manner as the list or tuple above.

        If the argument is a DBRef then it is resolved into a Document and the
        corresponding attributes are set.
        '''

        self.__schema__ = schema
        self.document = None
        self.targetid = None
        self.type = None
        dynamic_type = None

        if schema == any or any in schema:
            self.type = any
        elif id in schema:
            if not id in schema:
                raise SchemaTypeError(schema, 'Expt key.')
            value_schema = schema[id]
            if value_schema == any:
                self.type = any
            elif isinstance(value_schema,str):
                self.type = coconut.container.Document.__types__[value_schema]
            elif inspect.isclass(value_schema) and isinstance(value_schema,coconut.container.Document):
                self.type = value_schema
            else:
                raise SchemaTypeError (schema, 'Link schema id must map to Document, string or any, not %s' % value_schema)
        else:
            raise SchemaTypeError(schema,'Link schema must include "id" or "any" key.')

        # We can't validate manual references, so we just store them.
        if isinstance(target, ObjectId):
            self.targetid = str(target)
        elif isinstance(target,str):
            self.targetid = target
        elif isinstance(target,coconut.container.Document):
            self.document = target
            if not target.id: raise ValueError ('Cannot create link to unsaved document.')
            self.targetid = target.id
            dynamic_type = type(target)
        elif isinstance(target,Link):
            self.document = target.document
            self.targetid = target.targetid
            dynamic_type = type(target.type)
        elif isinstance(target,DBRef):
            self.targetid = target.id
            dynamic_type = coconut.container.Document.__types__[target.collection]
        elif isinstance(target,dict):
            self.targetid = target['id']
            dynamic_type = coconut.container.Document.__types__[target['collection']]
        elif isinstance(target,[list,tuple]):
            self.targetid = target[1]
            dynamic_type = coconut.container.Document.__types__[target[0]]

        if self.document and self.type != any:
            if not isinstance(self.document,self.type):
                raise ValidationTypeError (self.type,self.document)
        if dynamic_type:
            if self.type == any:
                self.type = dynamic_type
            elif self.type != dynamic_type:
                raise ValidationTypeError (self.type,dynamic_type)

        if self.type == any:
            raise ValueError ('Cannot create untyped link. Target must be typed or type specified by schema.')

    def __call__ (self):
        '''Dereference the link.'''
        return self.dereference()

    def dereference (self):
        '''Resolve the link and return the target document.'''

        if self.document: return self.document
        if self.type == any:
           raise ValueError ('Cannot follow untyped reference.')
        document = self.type[self.targetid]
        self.document = document
        return document

    def format_db (self):
        schema = self.__schema__
        if schema == any or schema[id] == any:
            # Create DBRef
            if self.type == any:
                raise ValueError ('Cannot create DBRef from untyped reference.')
            return SerialisableDBRef (self.type.__name__, self.targetid)
        else:
            # Create manual reference
            return SerialisableObjectId (self.targetid)

