from pymongo import MongoClient
import certifi

MONGO_URI = "mongodb+srv://admin:admin@cluster0.aasrm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "document_store"
COLLECTION_NAME = "chunks"

client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())

db = client[DB_NAME]
collection = db[COLLECTION_NAME]