from app import app
from bson import ObjectId
import logging
from typing import Optional, Tuple
import traceback
from .mongo import collection
import torch
from groq import Groq
from typing import List, Tuple
from bson import ObjectId
import traceback
from .pine import index, tokenizer, model
from .parser import parse_pdf, parse_docx
import json
from flask import Flask, request, jsonify

client = Groq(api_key="")

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
        file_content = ""
        if file.filename.endswith('.pdf'):
            file_content = parse_pdf(file)
        elif file.filename.endswith('.docx'):
            file_content = parse_docx(file)
        else:
            return {'success': False}, 401

        if not process_document(pathname, file_content):
            return {'success': False}, 401
    
    return {'success': True}, 200

def similarity_search(embedding):
    response = index.query(
        vector=embedding,
        top_k=5,
        include_values=True
    )
    
    response = json.loads(str(response).replace("'", '"'))
    return [r['id'] for r in response['matches']]

def retrieve_chunks(ids: List[str]):
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
            
    file_paths = [result[0] for result in results]
    chunks = [result[1] for result in results]
    
    return file_paths, chunks

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

@app.route('/submit_query', methods=['POST'])
def submit_query():
    data = request.get_json()
    
    if not data or "queries" not in data:
        return jsonify({"error": "No queries provided"}), 400

    queries = data["queries"]
    
    if not isinstance(queries, list):
        return jsonify({"error": "Queries should be a list"}), 400
    
    results = []

    for query in queries:
        embedding = embed_query(query)
        ids = similarity_search(embedding)
        file_paths, chunks = retrieve_chunks(ids)

        if not chunks:
            results.append({"query": query, "summary": "No relevant documents found."})
            continue

        summary = generate_summary(chunks)
        results.append({"query": query, "summary": summary})
    
    return jsonify({"results": results})

if __name__ == '__main__':
    pass
