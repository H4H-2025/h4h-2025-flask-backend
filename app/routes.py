# from app import app
from flask import request
from bson import ObjectId
import logging
from typing import Optional, Tuple
import traceback
from mongo import collection
import torch
from pine import index, tokenizer, model

# @app.route('/', methods=['GET'])
# def home_page():
#     return {'message': 'Hello, World!'}


def store_chunk_in_mongo(file_path, chunk):
    document = {
        "file_path": file_path,
        "content": chunk
    }
    result = collection.insert_one(document)
    return str(result.inserted_id)

def embed_chunk(chunk):
    tokens = tokenizer(chunk, return_tensors="pt", padding=True, truncation=True)

    with torch.no_grad():
        outputs = model(**tokens)

    embeddings = outputs.last_hidden_state.squeeze().flatten().tolist()
    return embeddings

def store_embedding(embeddings, id):
    index.upsert([(str(id), embeddings)])

def process_chunk(file_path, chunk):
    id = store_chunk_in_mongo(file_path, chunk)
    embeddings = embed_chunk(chunk)
    store_embedding(embeddings, id)
    return id



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

    # return {'success': True}

def similarity_search(embedding):
    response = index.query(namespace="ns1", vector=embedding, top_k=2, include_values=True, include_metadata=True,)
    context = ""
    for match in response['matches']:
        results = client['chunks']['shadcn'].find_one({ "_id" : ObjectId(match['id']) })
        content = results['chunk']
        context += content
        context += '\n\n'
    return context
    # call pinecone to get similar embeddings
    # return similar embeddings

def retrieve_chunks(ids):
    # for each id, retrieve chunk from pinecone
    # return chunks
    pass

def generate_summary(chunks):
    # feed chunks into llm
    # return summaries
    pass

def embed_query(query):
    return embed_chunk(query)

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
    chunk = "This is a test chunk"
    file_path = "test_file.txt"
    print(process_chunk(file_path, chunk))
