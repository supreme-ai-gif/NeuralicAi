# memory.py
import os
import uuid
from pinecone import Pinecone
from openai import OpenAI

# -------------------------------
# Pinecone setup
# -------------------------------
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "neuralic-memory"

# Create Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

# -------------------------------
# OpenAI setup for embeddings
# -------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# -------------------------------
# Store user message in Pinecone
# -------------------------------
def store_memory(user_id: str, text: str):
    """
    Convert text to embeddings and store in Pinecone.
    """
    # Get embeddings from OpenAI
    emb_resp = openai_client.embeddings.create(
        model="text-embedding-3-large",
        input=text
    )
    vector = emb_resp.data[0].embedding

    # Unique ID for each message
    vector_id = str(uuid.uuid4())

    # Upsert to Pinecone
    index.upsert([(vector_id, vector, {"user_id": user_id, "text": text})])

# -------------------------------
# Retrieve last N relevant messages
# -------------------------------
def get_memory(user_id: str, top_k: int = 5):
    """
    Retrieve top_k most relevant messages for a user from Pinecone.
    """
    # Create a dummy query embedding to search
    query_text = f"Retrieve conversation for {user_id}"
    emb_resp = openai_client.embeddings.create(
        model="text-embedding-3-large",
        input=query_text
    )
    query_vector = emb_resp.data[0].embedding

    # Query Pinecone
    result = index.query(vector=query_vector, top_k=top_k, include_metadata=True)

    memory = []
    for match in result.matches:
        if match.metadata.get("user_id") == user_id:
            memory.append(match.metadata.get("text"))

    return memory
