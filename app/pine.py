import pinecone
from pinecone import Pinecone, ServerlessSpec
from transformers import AutoTokenizer, AutoModel

pc = Pinecone(api_key="you-thought-lil-boi")
index = pc.Index("chunks")

tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
model = AutoModel.from_pretrained("bert-base-uncased")