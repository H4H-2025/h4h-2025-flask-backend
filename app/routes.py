from app import app
from flask import request, jsonify, make_response
from flask_cors import cross_origin
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
from io import BytesIO
from docx import Document

client = Groq(api_key="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")

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


@app.route('/embed_file', methods=['POST'])
def embed_file():
    file = request.data
    file_path = request.args.get('filename')
    file_type = request.args.get('type')

    return {'success': True}, 200
    if not file_path or not file_type:
        return make_response(jsonify({"message": "Filename and type are required"}), 400)

    # Log the content type and the first few bytes of the file content
    print(f"Content-Type: {file_type}")
    print(f"File Content (first 100 bytes): {file[:100]}")

    try:
        file_stream = BytesIO(file)
        doc = Document(file_stream)
        file_content = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    except Exception as e:
        print(f"Error processing docx file: {e}")
        return make_response(jsonify({"message": "Error processing docx file"}), 400)

    process_document(file_path, file_content)
    response = make_response(jsonify({"message": "File embedded successfully"}), 200)
    return response
        

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
            continue

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
    q = request.args.get('q')
    embedding = embed_query(q)
    ids = similarity_search(embedding)
    file_paths, chunks = retrieve_chunks(ids)
    summaries = generate_summary(chunks)
    resp = make_response(jsonify({"chunks": chunks, "summaries": summaries, "file_paths": file_paths}), 200)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

if __name__ == '__main__':
    pass
