from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

def get_db():
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise Exception("MONGO_URI not found in environment")

    client = MongoClient(mongo_uri)
    db = client["master_db"]
    return db
