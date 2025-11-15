# memory.py
import os
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI

# ---------------------------
# ENV VARIABLES
# ---------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX")  # your index name
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")  # aws or gcp region

if not all([OPENAI_API_KEY, PINECONE_API_KEY, PINECONE_INDEX, PINECONE_ENVIRONMENT]):
    raise Exception("Missing environment variables")

# ---------------------------
# INIT CLIENTS
# ---------------------------
pc = Pinecone(api_key=PINECONE_API_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# ---------------------------
# CREATE INDEX (IF MISSING)
# ---------------------------
if PINECONE_INDEX not in pc.list_indexes().names():
    pc.create_index(
        name=PINECONE_INDEX,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region=PINECONE_ENVIRONMENT
        )
    )

# ---------------------------
# CONNECT TO THE INDEX
# ---------------------------
index = pc.Index(PINECONE_INDEX)

# ---------------------------
# MEMORY CLASS
# ---------------------------
class MemoryDB:
    def __init__(self):
        self.index = index
        self.embed = openai_client

    def embed_text(self, text):
        """Generate embedding"""
        res = self.embed.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return res.data[0].embedding

    def store(self, user_id, text):
        """Store memory"""
        vec = self.embed_text(text)
        self.index.upsert([
            {
                "id": user_id,
                "values": vec,
                "metadata": {"text": text}
            }
        ])

    def query(self, text, top_k=5):
        """Semantic search in memory"""
        vec = self.embed_text(text)
        result = self.index.query(
            vector=vec,
            top_k=top_k,
            include_metadata=True
        )
        return result.matches
