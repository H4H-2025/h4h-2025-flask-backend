import pinecone
from pinecone import Pinecone, ServerlessSpec
from transformers import AutoTokenizer, AutoModel

pc = Pinecone(api_key="pcsk_5k68Ax_HVLwymDuXshHevSMQNHHowX2Npwap3h5ZBSBMubECmEUdLX9JAJGvB995a1noBq")
index = pc.Index("chunks")

tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
model = AutoModel.from_pretrained("bert-base-uncased")