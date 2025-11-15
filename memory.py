# memory.py
import os
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI

# ---------------------------
# ENVIRONMENT VARIABLES
# ---------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")  # e.g., "us-west1-gcp"
PINECONE_INDEX = os.getenv("PINECONE_INDEX")  # e.g., "neuralic-memory"

if not all([OPENAI_API_KEY, PINECONE_API_KEY, PINECONE_ENVIRONMENT, PINECONE_INDEX]):
    raise Exception("Missing Pinecone or OpenAI environment variables")

# ---------------------------
# INIT PINECONE
# ---------------------------
pc = Pinecone(api_key=PINECONE_API_KEY)

# Check if index exists, otherwise create
if PINECONE_INDEX not in pc.list_indexes().names():
    pc.create_index(
        name=PINECONE_INDEX,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",  # or gcp depending on your account
            region=PINECONE_ENVIRONMENT
        )
    )

index = pc.index(PINECONE_INDEX)

# ---------------------------
# INIT OPENAI EMBEDDINGS
# ---------------------------
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# ---------------------------
# MEMORY CLASS
# ---------------------------
class MemoryDB:
    def __init__(self):
        self.index = index
        self.embed = openai_client

    def embed_text(self, text: str):
        """Create vector embedding for text"""
        resp = self.embed.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return resp.data[0].embedding

    def store(self, user_id: str, text: str):
        """Store a message or memory in Pinecone"""
        vec = self.embed_text(text)
        self.index.upsert([(user_id, vec, {"text": text})])

    def query(self, user_id: str, top_k: int = 5):
        """Retrieve top-k related memories"""
        resp = self.index.query(
            vector=self.embed_text(user_id),
            top_k=top_k,
            include_metadata=True
        )
        return resp.matches
