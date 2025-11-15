# memory.py
import os
import pinecone
from openai import OpenAI

class MemoryDB:
    def __init__(self):
        pinecone.api_key = os.getenv("PINECONE_API_KEY")
        env = os.getenv("PINECONE_ENVIRONMENT")
        index_name = os.getenv("PINECONE_INDEX")

        pinecone.init(api_key=pinecone.api_key, environment=env)
        self.index = pinecone.Index(index_name)
        self.embed = OpenAI()

    def embed_text(self, text):
        resp = self.embed.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return resp.data[0].embedding

    def store(self, user_id, text):
        vec = self.embed_text(text)
        self.index.upsert([(user_id, vec, {"text": text})])
