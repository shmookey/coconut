coconut
=======

Object-Document Mapper for MongoDB and Python. 

Coconut provides a powerful and flexible schema syntax for Python objects that allows you to take advantage of MongoDB in a natural, pythonic way. 

Features
--------

- Deep object schemas
- Automatic versioning
- Transparent references
- Customisable ndexing
- Automatic revisioning
- History iterator

Get Started
-----------
```python
from pymongo import MongoClient
import coconut.container
# Set up Mongo client
coconut.container.Document.__db__ = MongoClient()['test']

# Declare a Document type and annotate it with a schema
class Person (coconut.container.Document):
    __schema__ = {
      'name': { str: any, 'index':'unique' },
      'age':  { int: any },
      'referer': { id: 'Person' },
   }     

# Create, update and save some instances
john = Person(name='Jonno',age=32)
john.name = 'Jonathan'                           # Use attribute-style access
john['name'] = 'John'                            # Or dict-style access
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
    print i # Prints 37,36,35,34,33
```

Schemas
-------

Coconut exposes most of its functionality through *schemas*, which tell Coconut how to interpret and validate your objects. A Coconut schema is simply a dictionary describing the object's attributes. The one exception is the *any* schema, which will validate against any object. Schemas must contain exactly one *data type* key in the form of the Python builtin which most closely corresponds to the kind of data the object contains. Currently supported data type keys are: *int*, *float*, *str*, *list*, *dict*, *id* and *any*.

The data type key maps to a *constraint* object. For most data types the constraint value must be *any*. For the *list* and *dict* data type, the constraint value is respectively a list or a dict. A constraint dict maps the keys that may appear in the dict being processed to the schema objects for those items. Each item in a constraint list is a schema for validating an item at that position in the list, unless the list schema has the *range: all* property set, which causes the first schema in the list to be applied to all items.

To use a schema, just set the *__schema__* attribute on a subclass of *Document*. If you don't need to set any other options, you can set __schema__ to the constraint object, rather than a full schema. The following two examples are equivalent:

```python
class MyDocument(Document):
    '''Using a full schema for __schema__.'''
    __schema__ = {
        dict: {
            'foo': { str: any },
            'bar': { str: any },
        }
    }

class MyDocument(Document):
    '''Using a constraint object for __schema__.'''
    __schema__ = {
        'foo': { str: any },
        'bar': { str: any },
    }
```

Revisioning
-----------

Coconut provides automatic revisioning for all fields and sub-fields of documents. Revisions are stored in the Revision collection. The history() method on any collection type (currently *Document*, *Dict* and *List*) returns an iterator over the collection or any key, which may be specified as an argument in MongoDB dot notation, e.g. Shape.Dimensions.Width.

Links
-----

Coconut can automatically reference and reference Documents for you using the *id* schema type. You can specify either the Document class name or *any* as the target and Coconut will store the minimum required information to make the reference unambiguous, i.e. *id: MyDocument* will store only the ID, whereas *id: any* will cause a full DBRef including the collection name to be stored.

Further Reading
---------------

Coconut offers a lot of cool functionality, but most of it isn't documented yet. Check out the tests folder for examples of all the different functionality available.


