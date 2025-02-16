from pymongo import MongoClient

MONGO_URI = ""
DB_NAME = "document_store"
COLLECTION_NAME = "chunks"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]