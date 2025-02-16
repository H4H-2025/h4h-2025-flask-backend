from app import app
from flask import request
from bson import ObjectId
import logging
from typing import Optional, Tuple
import traceback
from .mongo import collection
import torch
from openai import OpenAI
from typing import List, Tuple
from bson import ObjectId
import traceback
client = OpenAI(api_key="")
from .pine import index, tokenizer, model
from .parser import parse_pdf
import json

@app.route('/', methods=['GET'])
def home_page():
    return {'message': 'Hello, World!'}


def store_chunk_in_mongo(file_path, chunk):
    document = {
        "file_path": file_path,
        "content": chunk
    }
    result = collection.insert_one(document)
    return str(result.inserted_id)

def embed_chunk(chunk):
    tokens = tokenizer(chunk, return_tensors="pt", padding=True, truncation=True, max_length=512)

    with torch.no_grad():
        outputs = model(**tokens)

    embeddings = outputs.last_hidden_state.mean(dim=1).squeeze().tolist()
    return embeddings

def store_embedding(embeddings, id):
    index.upsert([(str(id), embeddings)])

def process_chunk(file_path, chunk):
    id = store_chunk_in_mongo(file_path, chunk)
    embeddings = embed_chunk(chunk)
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
    chunks = chunk_document(file)
    for chunk in chunks:
        process_chunk(file_path, chunk)
    return {'success': True}

@app.route('/embed_folder', methods=['POST'])
def embed_folder():
    files = request.files.getlist('files')
    pathnames = request.form.getlist('pathnames')

    for file, pathname in zip(files, pathnames):
        file_content = parse_pdf(file)
        if not process_document(pathname, file_content):
            return {'success': False}, 401
    
    return {'success': True}, 200

def similarity_search(embedding):
    response = index.query(
        vector=embedding,
        top_k=2,
        include_values=True
    )
    
    response = json.loads(str(response).replace("'", '"'))
    return [r['id'] for r in response['matches']]

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

def generate_summary():
    # feed chunks into llm
    # return summaries
    summaries = []
    
    for chunk in chunks:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Generate a concise summary of the following text knowing that a scientist is reading it."},
                {"role": "user", "content": chunk}
            ],
            temperature=0.7,
            max_tokens=150
        )
        summaries.append(response.choices[0].message.content)
    
    return summaries

def embed_query(query):
    return embed_chunk(query)

@app.route('/submit_query', methods=['GET'])
def submit_query():
    q = request.args.get('q')
    embedding = embed_query(q)
    ids = similarity_search(embedding)

    call retrieve_chunks(ids)

    # call generate_summary(chunks)

    # return chunks, summaries, file_paths

    return {'success': True}

if __name__ == '__main__':
    file_path = "test.txt"
    file = "This is a test file"
    print(process_document(file_path, file))