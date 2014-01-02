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
import coconut.container
# Set up Mongo client
coconut.container.Document.set_db({'db':'MyDatabase'})

# Declare a Document type and annotate it with a schema
class Person (coconut.container.Document):
    __schema__ = {
        'name':    { str: any, 'index':'unique' },
        'age':     { int: any },
        'referer': { id: 'Person' },
    }

# Create, update and save some instances
john = Person(name='Jonno',age=32)
john.name = 'Jonathan'  # Use attribute-style access
john['name'] = 'John'   # Or dict-style access
john.save()
fred = Person({'name':'Fred','age':29,'referer':john})
fred.save()

# Find records
john2 = Person[john.id]              # By array-style access
fred2 = Person.find({'_id':fred.id}) # By MongoDB query
john3 = fred2.referer()              # By link dereferencing

# View history
for i in range(5):
    john.age += 1
    john.save()
history = john.history('age')
for i in history:
    print i # Prints 36,35,34,33,32
```

Further Reading
---------------

Coconut offers a lot of cool functionality, but most of it isn't documented yet. Check out the tests folder for examples of all the different functionality available.


