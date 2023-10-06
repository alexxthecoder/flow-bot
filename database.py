import pandas as pd
from pymongo import MongoClient

def get_store():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['test_database']
    store = db['test']
    return store