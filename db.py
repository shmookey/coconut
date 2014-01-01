''' db.py -- Coconut MongoDB connection.
Author: Luke Williams <shmookey@shmookey.net>

Distributed under the MIT license, see LICENSE file for details.
'''

from coconut.error import *

from bson.objectid import ObjectId
from bson.dbref import DBRef

class SerialisableDBRef (DBRef):
    def __json__ (self):
        return {'collection':self.collection,'id':self.id}

class SerialisableObjectId (ObjectId):
    def __json__ (self):
        return str(self)

