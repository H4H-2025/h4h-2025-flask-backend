from app import app
from flask import request
import os

@app.route('/', methods=['GET'])
def home_page():
    return {'message': 'Hello, World!'}

def store_chunk_in_mongo(chunk):
    pass

def embed_chunk(chunk):
    pass

def store_embedding(embedding, id):
    pass

def process_chunk(chunk):
    chunk = "This is a test chunk"
    # call store_chunk_in_mongo(chunk)

    # call embed_chunk(chunk)

    # call store_embedding(embedding, id)
    pass

def process_document(file, file_path):
    # chunk document

    # for each chunk, call process_chunk(chunk)

    # return 
    pass

@app.route('/embed_folder', methods=['POST'])
def embed_folder():

    if request.method == "POST":
        if "files" not in request.files:
            return "No file part"

    # for each file, call process_document(file, file_path)

    return {'success': True}


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

@app.route('/submit_query', methods=['GET'])
def submit_query():
    # get query from request

    # call embed_query(query)

    # call similarity_search(embedding)

    # call retrieve_chunks(ids)

    # call generate_summary(chunks)

    # return chunks, summaries, file_paths

    return {'success': True}