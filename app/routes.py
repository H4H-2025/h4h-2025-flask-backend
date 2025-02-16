# from app import app
from flask import request
from bson import ObjectId
import logging
from typing import Optional, Tuple
import traceback
from mongo import collection
import torch
from pine import index, tokenizer, model
from groq import Groq
import os
from typing import List, Tuple
from bson import ObjectId
import traceback

client = Groq(api_key="")

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

def store_chunk_in_pinecone(chunk):
    tokens = tokenizer(chunk, return_tensors="pt", padding=True, truncation=False)

    with torch.no_grad():
        outputs = model(**tokens)

    embeddings = outputs.last_hidden_state.squeeze().flatten().tolist()
    return embeddings

def store_embedding(embeddings, id):
    index.upsert([(str(id), embeddings)])

def process_chunk(file_path, chunk):
    id = store_chunk_in_mongo(file_path, chunk)
    embeddings = store_chunk_in_pinecone(chunk)
    store_embedding(embeddings, id)
    return id

def chunk_document(file):
    tokens = tokenizer.tokenize(file)
    chunks = []
    for i in range(0, len(tokens), 512 - 50):
        chunk = tokens[i:i + 512]
        chunks.append(tokenizer.convert_tokens_to_string(chunk))
    return chunks

def process_document(file_path, file):
    # chunk_document(file)

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

def retrieve_chunks(ids: List[str]) -> List[Tuple[str, str]]:
    try:
        object_ids = [ObjectId(id_str) for id_str in ids]
        
        chunks = collection.find({'_id': {'$in': object_ids}})
        
        chunks_list = list(chunks)
        
        chunks_dict = {
            str(chunk['_id']): (chunk['file_path'], chunk['content']) 
            for chunk in chunks_list
        }
        
        results = []
        for id_str in ids:
            if id_str in chunks_dict:
                results.append(chunks_dict[id_str])
            else:
                print(f"Document with id {id_str} not found")
                results.append((None, None))
                
        return results
        
    except Exception as e:
        print(f"Error retrieving chunks: {str(e)}")
        traceback.print_exc()
        return [(None, None)] * len(ids)

def generate_summary(chunks):
    summaries = []
    
    for chunk in chunks:
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",  
            messages=[
                {"role": "system", "content": "You are a direct summarizer. Provide only a concise summary of the input text without any prefixes, meta-commentary, or formatting. If the input is too short or lacks substance, simply return 'Input too brief to summarize.'"},
                {"role": "user", "content": chunk}
            ],
            temperature=0.7,
            max_tokens=150
        )
        summaries.append(response.choices[0].message.content)
    
    return summaries

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
    # pass