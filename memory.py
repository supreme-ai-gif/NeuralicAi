# memory.py
import os
import pinecone
from openai import OpenAI

# ---------------------------
# CHECK ENVIRONMENT VARIABLES
# ---------------------------
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
PINECONE_INDEX = os.getenv("PINECONE_INDEX")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not all([PINECONE_API_KEY, PINECONE_ENVIRONMENT, PINECONE_INDEX, OPENAI_API_KEY]):
    raise Exception("Missing Pinecone or OpenAI environment variables")

# ---------------------------
# INITIALIZE PINECONE
# ---------------------------
pinecone.init(
    api_key=PINECONE_API_KEY,
    environment=PINECONE_ENVIRONMENT
)

# Connect to index (will raise error if it doesn't exist)
index = pinecone.Index(PINECONE_INDEX)

# ---------------------------
# INITIALIZE OPENAI EMBEDDINGS
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
