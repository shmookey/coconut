''' container.py -- Coconut container types
Author: Luke Williams <shmookey@shmookey.net>

Distributed under the MIT license, see LICENSE file for details.
'''

from coconut.error import *
from coconut.primitive import Element
from coconut.db import get_db, SerialisableDBRef, SerialisableObjectId
import coconut.schema
import coconut.element

from bson.objectid import ObjectId
from bson.dbref import DBRef

import copy, time

class MutableElement (Element):
    '''Base class for mutable container types.

    The __unsaved__ attribute implements copy-on-write.
    '''

    def __init__ (self, parent, schema):
        Element.__init__ (self)
        if schema: self.__schema__ = schema
        self.__unsaved__ = {}
        if type(self) == Element:
            raise TypeError ('Element type must not be instantiated directly, use a derived class.')
        if not isinstance(parent,Element):
            raise TypeError ('Parent must be of type Element, not %s' % str(type(parent)))
        self.parent = parent

    def get_document (self):
        if isinstance(self.parent, Document):
            return self.parent
        elif isinstance(self.parent, Element):
            return self.parent.get_document()
        else:
            raise TypeError ('Parent must be of type Element, not %s' % str(type(self.parent)))

    def flush (self):
        '''Recursively flush unsaved changes.'''

        raise NotImplementedError()

class Dict (MutableElement, dict):
    '''Database-aware dict type.'''

    def __init__ (self, parent, schema=None):
        dict.__init__(self)
        MutableElement.__init__ (self, parent, schema)
        self.__unsaved__ = None

    # Descriptors

    def __repr__ (self):
        if self.__unsaved__ == None: return dict.__repr__(self)
        else: return dict.__repr__(self.__unsaved__)

    def __contains__ (self, key):
        current = self.__unsaved__ if self.__unsaved__ != None else self
        return dict.__contains__(current,key)

    def __str__ (self):
        current = self.__unsaved__ if self.__unsaved__ != None else self
        return dict.__str__(current,key)

    # Accessors

    def __getitem__ (self, key):
        '''Return the value of an item in the dict.'''

        current = self.__unsaved__ if self.__unsaved__ != None else self
        item = dict.__getitem__(current,key)
        if isinstance(item,MutableElement):
            return item
        return item

    def items (self):
        current = self.__unsaved__ if self.__unsaved__ != None else self
        return dict.items(current)

    def iteritems (self):
        current = self.__unsaved__ if self.__unsaved__ != None else self
        return dict.iteritems(current)

    # Mutators

    def __setitem__ (self, key, value):
        '''Set the value of an item in the dict.

        Implements copy-on-write until flushed.
        '''

        if self.__unsaved__ == None: self.__unsaved__ = dict(self)
        if self.__schema__ == any:
            self.__unsaved__[key] = coconut.schema.Schema.import_element(value,any,self)
            return
        schema = self.__schema__
        traverse = schema.get('traverse',True)
        if schema[dict] == any:
            if traverse:
                element = coconut.schema.Schema.import_element(value,any,self)
            else:
                element = value
        else:
            if not key in schema[dict]:
                raise ValidationKeyError (key)
            item_schema = schema[dict][key]
            if traverse:
                element = coconut.schema.Schema.import_element(value, item_schema, self)
            else: 
                element = value
        self.__unsaved__[key] = element

    def update (self, dct):
        '''Replace keys with values from dct.

        Changes are buffered until flushed.
        '''

        if self.__unsaved__ == None: self.__unsaved__ = dict(self)
        for key, value in dct.items():
            if self.__schema__[dict] == any:
                element = coconut.schema.Schema.import_element(value, any, self)
            else:
                item_schema = self.__schema__[dict][key]
                element = coconut.schema.Schema.import_element(value, item_schema, self)
            self.__unsaved__[key] = element

    # Database methods

    def flush (self):
        '''Recursively flush unsaved changes.'''

        if self.__unsaved__ != None:
            dict.__init__(self, self.__unsaved__)
            self.__unsaved__ = None
        for key, item in self.items():
            if isinstance(item,MutableElement):
                item.flush()

    def get_changes (self):
        '''Recursively generate and return a list of unsaved changes.'''
        sets = {}
        unsets = {}
        current = self.__unsaved__ if self.__unsaved__ != None else self
        old = dict(self)
        
        # Check for dropped keys
        if current != self:
            for key in old:
                if not key in current:
                    unsets[key] = ''
       
        for key, current_value in current.items():
            key_schema = self.__schema__[dict][key]
            # Is the value a primitive type?
            if not isinstance(current_value,MutableElement):
                if key not in old or not old[key] == current_value:
                    sets[key] = coconut.schema.Schema.export_element(current_value,key_schema)
                continue
            
            traverse = key_schema.get('traverse',True)
            if not traverse:
                # TODO: Check if there are actually any changes
                sets[key] = current_value
                continue

            # Don't look at subkeys of new items, just insert the whole dict.
            if key not in old:
                child_item = coconut.schema.Schema.export_element(current_value)
                sets[key] = child_item
                continue

            # Are there any changes in the child container?
            child_sets, child_unsets = current_value.get_changes()
            for child_key, child_value in child_sets.items():
                qualified_key = '%s.%s' % (key,child_key)
                sets[qualified_key] = child_value
            for child_key, child_value in child_unsets.items():
                qualified_key = '%s.%s' % (key,child_key)
                unsets[qualified_key] = child_value

        return sets, unsets

class List (MutableElement, list):
    '''Database-aware list type.'''

    def __init__ (self, parent, schema=None):
        list.__init__(self)
        MutableElement.__init__ (self, parent, schema)
        self.__unsaved__ = None

    # Descriptors

    def __repr__ (self):
        if self.__unsaved__ == None: return list.__repr__(self)
        else: return list.__repr__(self.__unsaved__)

    def __contains__ (self, key):
        current = self.__unsaved__ if self.__unsaved__ != None else self
        return list.__contains__(current,key)

    def __iter__ (self):
        current = self.__unsaved__ if self.__unsaved__ != None else self
        return list.__iter__(current)

    def __len__ (self):
        current = self.__unsaved__ if self.__unsaved__ != None else self
        return list.__len__(current)

    # Accessors

    def __getitem__ (self, key):
        '''Return the value of an item in the list.'''

        current = self.__unsaved__ if self.__unsaved__ != None else self
        item = list.__getitem__(current,key)
        if isinstance(item,MutableElement):
            return item
        return item

    # Mutators

    def __setitem__ (self, idx, value):
        '''Set the value of an item in the list.

        Implements copy-on-write until flushed.
        '''

        if self.__unsaved__ == None: self.__unsaved__ = list(self)
        if self.__schema__ == any:
            self.__unsaved__[key] = coconut.schema.Schema.import_element(value,any,self)
            return
        schema = self.__schema__
        traverse = schema.get('traverse',True)
        item_schema = coconut.schema.Schema.get_list_index_schema(idx,schema)
        if traverse:
            element = coconut.schema.Schema.import_element(value,item_schema,self)
        else:
            element = value
        self.__unsaved__[key] = element

    def append (self, value):
        '''Add an item to the end of a list.'''
        
        if self.__unsaved__ == None: self.__unsaved__ = list(self)
        if self.__schema__ == any:
            self.__unsaved__.append(coconut.schema.Schema.import_element(value,any,self))
            return
        schema = self.__schema__
        traverse = schema.get('traverse',True)
        idx = len(self.__unsaved__)
        item_schema = coconut.schema.Schema.get_list_index_schema(idx, schema)
        if traverse:
            element = coconut.schema.Schema.import_element(value,item_schema,self)
        else:
            element = value
        self.__unsaved__.append(element)

    # Database methods

    def flush (self):
        '''Recursively flush unsaved changes.'''

        if self.__unsaved__ != None:
            list.__init__(self, self.__unsaved__)
            self.__unsaved__ = None
        for item in self:
            if isinstance(item,MutableElement):
                item.flush()

    def get_changes (self):
        '''Recursively generate and return a list of unsaved changes.'''
        sets = {}
        unsets = {}
        current = self.__unsaved__ if self.__unsaved__ != None else self
        old = list(self)
        schema = self.__schema__
        
        # Rebuild the whole list if the length has changed.
        if len(current) != len(old):
            sets = {'': coconut.schema.Schema.export_element(self,schema)}
            return sets, unsets

        for i, current_value in enumerate(current):
            if schema == any:
                key_schema = any
            elif schema[list] == any:
                key_schema = any
            elif range in schema and schema[range] == all:
                key_schema = schema[list][0]
            else:
                key_schema = schema[list][i]

            # Is the value a primitive type?
            if not isinstance(current_value,MutableElement):
                if key not in old or not old[key] == current_value:
                    sets[key] = coconut.schema.Schema.export_element(current_value,key_schema)
                continue
            
            traverse = key_schema.get('traverse',True)
            if not traverse:
                # TODO: Check if there are actually any changes
                sets[key] = current_value
                continue
            if key not in old:
                child_item = coconut.schema.Schema.export_element(current_value)
                sets[key] = child_item
                continue
            
            child_sets, child_unsets = current_value.get_changes()

            # An empty string key indicates the child wants to be rebuilt
            if len(child_sets) == 1 and '' in child_sets:
                sets[key] = child_sets['']
                continue
            
            # Are there any changes in the child container?
            for child_key, child_value in child_sets.items():
                qualified_key = '%i.%s' % (i,child_key)
                sets[qualified_key] = child_value
            for child_key, child_value in child_unsets.items():
                qualified_key = '%i.%s' % (i,child_key)
                unsets[qualified_key] = child_value

        return sets, unsets

class DocumentClass (type):
    def __new__ (cls, clsname, bases, dct):
        if '__schema__' in dct:
            if not dict in dct['__schema__']:
                dct['__schema__'] = {dict:dct['__schema__']}

        newcls = type.__new__ (cls, clsname, bases, dct)
        if clsname == 'Document': return newcls
        
        # Register the class and DB with Document
        Document.__types__[clsname] = newcls
        newcls.__db__ = get_db()[clsname]
        
        return newcls

    def __getitem__ (cls, id):
        '''Retrieve a Document from the database by ID.'''

        doc = None
        if isinstance(id,str):
            doc = cls.__db__.find_one({'_id':ObjectId(id),'__active__':True})
        elif isinstance(id,unicode):
            doc = cls.__db__.find_one({'_id':ObjectId(id),'__active__':True})
        elif isinstance(id,coconut.element.Link):
            return id()
        elif isinstance(id,ObjectId):
            doc = cls.__db__.find_one({'_id':id,'__active__':True})
        else:
            raise TypeError ('ID must be of type str, ObjectId or Link, not %s' % type(id).__name__)
        if not doc:
            raise DocumentNotFound ('Could not find document ID: %s' % str(id))
        return cls(doc)

    def find_first (cls, criteria):
        criteria['__active__'] = True
        doc = cls.__db__.find_one(criteria)
        if not doc: raise DocumentNotFound (criteria)
        return cls(doc)

    def find (cls, criteria={}, limit=0):
        '''Get all matching documents.'''
        #TODO: Implement limits higher than 1
        criteria['__active__'] = True
        if limit == 1: return cls.find_first(criteria)
        doclist = cls.__db__.find(criteria)
        objlist = [cls(doc) for doc in doclist]
        return objlist

class Document (Dict):
    __metaclass__ = DocumentClass
    __types__ = {}
    __schema__ = { any: any }
    
    def __init__ (self, *args, **kwargs):
        if len(args) > 1 or (len(args) > 0 and kwargs):
            raise ValueError ('Document must be initialised with either one positional argument or keyword arguments.')
        Dict.__init__(self, self)
        if args: data = args[0]
        else: data = kwargs
        if '_id' in data:
            self.id = str(data['_id'])
            del data['_id']
        else:
            self.id = None
        if '__active__' in data:
            self.__active__ = data['__active__']
            del data['__active__']
        
        for key,value in data.items():
            self[key] = value
        # Check for default values
        for key,item_schema in self.__schema__[dict].items():
            if key not in self:
                if isinstance(item_schema,dict) and 'default' in item_schema:
                    self[key] = copy.deepcopy(item_schema['default'])
                else:
                    self[key] = None

    def __repr__ (self):
        return '%s(%s)' % (type(self).__name__,Dict.__repr__(self))

    # Accessors

    def __getattr__ (self, attr):
        if not attr in self:
            raise AttributeError(attr)
        return self[attr]

    # Mutators

    def __setattr__ (self, attr, value):
        if attr[0] == '_' or not attr in self.__schema__[dict]:
            Dict.__setattr__(self, attr, value)
        else:
            self[attr] = value

    # Database operations

    def save (self):
        sets, unsets = self.get_changes()
        query = {'$set': sets.copy(), '$unset': unsets.copy()}
        if self.id:
            self.__db__.update({'_id':ObjectId(self.id)}, query)
        else:
            query['$set']['__active__'] = True
            docid = self.__db__.insert(query['$set'])
            self.id = str(docid)
        self.flush()
        event_query = {'set': sets.copy(), 'unset': unsets.copy()}
        # Write change event
        if isinstance(self,Revision): return
        event = Revision(item=self,changes=event_query,date=int(time.time()))
        event.save()

    def remove (self):
        self.__collection__.update ({'_id':self.id},{'$set':{'__active__':False}})
        self.id = None

class Revision (Document):
    '''A change event to a document.'''

    __schema__ = {dict:{
      'item':    { id:   any },
      'changes': { dict: any, 'traverse':False },
      'date':    { int:  any },
    }}


