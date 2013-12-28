''' db.py -- Coconut MongoDB connection.
Author: Luke Williams <shmookey@shmookey.net>

Distributed under the MIT license, see LICENSE file for details.
'''

from coconut.error import *

from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.dbref import DBRef

db = None

def get_db ():
    global db
    if not db:
        db = MongoClient().scalpel
    return db

class SerialisableDBRef (DBRef):
    def __json__ (self):
        return {'collection':self.collection,'id':self.id}

class SerialisableObjectId (ObjectId):
    def __json__ (self):
        return str(self.id)

