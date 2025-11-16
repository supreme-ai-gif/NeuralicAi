import os
import uuid
from openai import OpenAI
from pinecone import Pinecone

# -------------------------
# Pinecone setup
# -------------------------
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "neuralic-memory"

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(name=INDEX_NAME)

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------------
# Store and get memory
# -------------------------
def store_memory(user_id: str, text: str):
    emb_resp = openai_client.embeddings.create(
        model="text-embedding-3-large",
        input=text
    )
    vector = emb_resp.data[0].embedding
    vector_id = str(uuid.uuid4())
    index.upsert([(vector_id, vector, {"user_id": user_id, "text": text})])

def get_memory(user_id: str, top_k: int = 5):
    query_text = f"Retrieve conversation for {user_id}"
    emb_resp = openai_client.embeddings.create(
        model="text-embedding-3-large",
        input=query_text
    )
    query_vector = emb_resp.data[0].embedding
    result = index.query(vector=query_vector, top_k=top_k, include_metadata=True)
    memory = [m.metadata["text"] for m in result.matches if m.metadata.get("user_id") == user_id]
    return memory
