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

Access Coconut's functionality by subclassing the *Document* type. Initialise *Document* with your database name and away you go:

```python
import coconut.container
# Set up database
coconut.container.Document.set_db({'db':'MyDatabase'})

# Declare a Document type
class MyDocument (coconut.container.Document):
    pass

# Create some Document instances
doc1 = MyDocument()
doc1['foo'] = 'bar'
doc1.save()

doc2 = MyDocument()

doc2 = MyDocument[doc.id]
print doc2['foo'] # Prints 'bar'
```

Further Reading
---------------

Coconut offers a lot of cool functionality, but most of it isn't documented yet. Check out the tests folder for examples of all the different functionality available.


