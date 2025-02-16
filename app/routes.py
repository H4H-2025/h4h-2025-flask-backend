# from app import app
from flask import request
import os
from pymongo import MongoClient
from bson import ObjectId
import logging
from typing import Optional, Tuple
import traceback
from datetime import datetime  # Added this import

# @app.route('/', methods=['GET'])
# def home_page():
#     return {'message': 'Hello, World!'}

def store_chunk_in_mongo(file_path: str, chunk: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Store a document chunk in MongoDB with the associated file path.
    
    Args:
        file_path (str): Path of the file the chunk belongs to
        chunk (str): The actual content of the chunk
        
    Returns:
        Tuple[bool, Optional[str], Optional[str]]: (success, document_id, error_message)
    """
    
    # Input validation
    if not file_path or not isinstance(file_path, str):
        return False, None, "Invalid file_path: must be a non-empty string"
    
    if not chunk or not isinstance(chunk, str):
        return False, None, "Invalid chunk: must be a non-empty string"
    
    # MongoDB connection settings
    MONGO_URI = "mongodb+srv://admin:admin@cluster0.aasrm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    DB_NAME = "document_store"
    COLLECTION_NAME = "chunks"
    
    client = None
    try:
        # Establish connection
        client = MongoClient(MONGO_URI)
        
        # Test connection
        client.admin.command('ping')
        
        # Get database and collection
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        # Prepare document
        document = {
            "file_path": file_path,
            "content": chunk,
            "created_at": datetime.utcnow()
        }
        
        # Insert document
        result = collection.insert_one(document)
        
        # Check if insertion was successful
        if result.inserted_id:
            return True, str(result.inserted_id), None
        else:
            return False, None, "Failed to insert document"
            
    except Exception as e:
        error_message = f"Error storing chunk: {str(e)}\n{traceback.format_exc()}"
        logging.error(error_message)
        
        # Attempt rollback if we have a client and the error occurred after insertion
        if client and 'result' in locals() and result.inserted_id:
            try:
                collection.delete_one({"_id": result.inserted_id})
                logging.info(f"Successfully rolled back insertion of document {result.inserted_id}")
            except Exception as rollback_error:
                logging.error(f"Failed to rollback changes: {str(rollback_error)}")
        
        return False, None, error_message
        
    finally:
        # Always close the connection
        if client:
            client.close()

def embed_chunk(chunk):
    pass

def store_embedding(embedding, id):
    pass

def process_chunk(chunk):
    # id = store_chunk_in_mongo(chunk)

    # call store_chunk_in_mongo(chunk)

    # call embed_chunk(chunk)

    # call store_embedding(embedding, id)
    pass

def process_document(file, file_path):
    # chunk document

    # for each chunk, call process_chunk(chunk)

    # return 
    pass

# @app.route('/embed_folder', methods=['POST'])
# def embed_folder():

#     if request.method == "POST":
#         if "files" not in request.files:
#             return "No file part"

#     # for each file, call process_document(file, file_path)

#     return {'success': True}


def embed_query(query):
    # embed query
    # return embedding
    pass

def similarity_search(embedding):
    # call pinecone to get similar embeddings
    # return similar embeddings
    pass

def retrieve_chunks(ids):
    # for each id, retrieve chunk from pinecone
    # return chunks
    pass

def generate_summary(chunks):
    # feed chunks into llm
    # return summaries
    pass

# @app.route('/submit_query', methods=['GET'])
# def submit_query():
    # get query from request

    # call embed_query(query)

    # call similarity_search(embedding)

    # call retrieve_chunks(ids)

    # call generate_summary(chunks)

    # return chunks, summaries, file_paths

    return {'success': True}

if __name__ == '__main__':
    file_path = "test/test_chunk"
    chunk = "This is a test chunk"
    store_chunk_in_mongo(file_path, chunk)