import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

_client = None

def _get_collection():
    global _client
    uri = os.environ.get("MONGODB_URI")
    if not uri:
        raise EnvironmentError("MONGODB_URI is not set. Add it to a .env file or your environment.")
    if _client is None:
        _client = MongoClient(uri)
    db = _client["inventorytracker"]
    return db["optimization"]

def save(document_id, A, b):
    col = _get_collection()
    col.replace_one(
        {"_id": document_id},
        {"_id": document_id, "A": A, "b": b},
        upsert=True,
    )

def load(document_id):
    col = _get_collection()
    doc = col.find_one({"_id": document_id})
    if doc is None:
        raise FileNotFoundError(f"No document found with id '{document_id}'.")
    return doc["A"], doc["b"]
