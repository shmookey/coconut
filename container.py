''' container.py -- Coconut container types
Author: Luke Williams <shmookey@shmookey.net>

Distributed under the MIT license, see LICENSE file for details.
'''

from coconut.primitive import Element
from coconut.db import SerialisableDBRef, SerialisableObjectId
import coconut.schema
import coconut.element
import coconut.error

from bson.objectid import ObjectId
from bson.dbref import DBRef
import pymongo.errors

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

    def export (self):
        '''Return a deep copy of the element suitable for serialisation.'''
        
        return coconut.schema.Schema.export_element(self)

    def history (self, key=None):
        '''Return a history iterator for the container or one of its keys.'''

        return coconut.revision.History(self, key)

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
        return dict.__str__(current)

    def __len__ (self):
        current = self.__unsaved__ if self.__unsaved__ != None else self
        return dict.__len__(current)

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
        schema = self.__schema__
        if schema == any or any in schema or schema[dict] == any or any in self.__schema__[dict]:
            self.__unsaved__[key] = coconut.schema.Schema.import_element(value,any,self)
            return
        traverse = schema.get('traverse',True)
        if schema[dict] == any:
            if traverse:
                element = coconut.schema.Schema.import_element(value,any,self)
            else:
                element = value
        else:
            if not key in schema[dict]:
                raise coconut.error.ValidationKeyError (key)
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
        schema = self.__schema__

        # Check for dropped keys
        if current != self:
            for key in old:
                if not key in current:
                    unsets[key] = ''
       
        for key, current_value in current.items():
            if schema == any or any in schema or schema[dict] == any or any in schema[dict]:
                key_schema = any
            else:
                key_schema = schema[dict][key]
            # Is the value a primitive type?
            if not isinstance(current_value,MutableElement):
                if key not in old or not old[key] == current_value:
                    sets[key] = coconut.schema.Schema.export_element(current_value,key_schema)
                continue
            
            traverse = key_schema.get('traverse',True)
            if not traverse:
                # TODO: Check if there are actually any changes
                # For now it seems that we do actually have to traverse everything when exporting
                sets[key] = coconut.schema.Schema.export_element(current_value,key_schema)
                continue

            # Don't look at subkeys of new items, just insert the whole dict.
            if key not in old:
                child_item = coconut.schema.Schema.export_element(current_value)
                sets[key] = child_item
                continue

            # Are there any changes in the child container?
            child_sets, child_unsets = current_value.get_changes()

            if child_sets: sets[key] = child_sets
            if child_unsets: unsets[key] = child_unsets
            continue
            # TODO: can probably scrap the rest of this?
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
                if i >= len(old) or not old[i] == current_value:
                    sets[i] = coconut.schema.Schema.export_element(current_value,key_schema)
                continue
            
            traverse = key_schema.get('traverse',True)
            if not traverse:
                # TODO: Check if there are actually any changes
                sets[i] = current_value
                continue
            if i >= len(old):
                child_item = coconut.schema.Schema.export_element(current_value)
                sets[i] = child_item
                continue
            
            child_sets, child_unsets = current_value.get_changes()
            sets[i] = child_sets
            unsets[i] = child_unsets
            continue
            # TODO: can probably scrap the rest of this?
            # An empty string key indicates the child wants to be rebuilt
            if len(child_sets) == 1 and '' in child_sets:
                sets[i] = child_sets['']
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
        
        return newcls

    def __getitem__ (cls, id):
        '''Retrieve a Document from the database by ID.'''

        doc = None
        clsname = cls.__name__
        if isinstance(id,str):
            doc = cls.__db__[clsname].find_one({'_id':ObjectId(id),'__active__':True})
        elif isinstance(id,unicode):
            doc = cls.__db__[clsname].find_one({'_id':ObjectId(id),'__active__':True})
        elif isinstance(id,coconut.element.Link):
            return id()
        elif isinstance(id,ObjectId):
            doc = cls.__db__[clsname].find_one({'_id':id,'__active__':True})
        else:
            raise TypeError ('ID must be of type str, ObjectId or Link, not %s' % type(id).__name__)
        if not doc:
            raise coconut.error.DocumentNotFound ('Could not find document ID: %s' % str(id))
        return cls(doc)

    def find_first (cls, criteria):
        '''Return the first element matching the provided criteria.'''

        criteria['__active__'] = True
        clsname = cls.__name__
        doc = cls.__db__[clsname].find_one(criteria)
        if not doc: raise coconut.error.DocumentNotFound (criteria)
        return cls(doc)

    def find (cls, criteria={}, limit=None, sort=[]):
        '''Get all matching documents.'''

        criteria['__active__'] = True
        clsname = cls.__name__
        if limit:
            doclist = cls.__db__[clsname].find(criteria, limit=limit)
        else:
            doclist = cls.__db__[clsname].find(criteria)
        if sort: doclist.sort(*sort)
        objlist = [cls(doc) for doc in doclist]
        return objlist

    def ensure_indexes (cls):
        '''Ensure indexes defined on the Document schema exist in the database.

        Currently only indexes on top-level keys are supported.
        '''

        clsname = cls.__name__
        for (key,val) in cls.__schema__[dict].items():
            if isinstance(val,dict):
                index = val.get('index',None)
                if not index: continue
                opts = {}
                if index == 'unique': opts['unique'] = True
                cls.__db__[clsname].ensure_index(key, **opts)

class Document (Dict):
    __metaclass__ = DocumentClass
    __types__ = {}
    __schema__ = { any: any }
    
    def __init__ (self, *args, **kwargs):
        # Dirty hack to resolve cyclic inheritance imports
        import coconut.revision
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
            if key == any: continue
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
        clsname = type(self).__name__
        try:
            if self.id:
                self.__db__[clsname].update({'_id':ObjectId(self.id)}, query)
            else:
                query['$set']['__active__'] = True
                docid = self.__db__[clsname].insert(query['$set'])
                self.id = str(docid)
        except pymongo.errors.DuplicateKeyError as e:
            raise coconut.error.UniqueIndexViolation(str(e))

        self.flush()
        event_query = {'set': sets.copy(), 'unset': unsets.copy()}
        # Write change event
        if isinstance(self,coconut.revision.Revision): return
        event = coconut.revision.Revision(item=self,changes=event_query,date=time.time())
        event.save()

    def remove (self):
        self.__collection__.update ({'_id':self.id},{'$set':{'__active__':False}})
        self.id = None

    def export (self):
        '''Return a deep copy of the Document suitable for serialisation.'''
        
        doc = coconut.schema.Schema.export_element(self)
        doc['id'] = self.id
        return doc

