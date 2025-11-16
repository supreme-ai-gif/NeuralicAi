# decision_making.py
import os
from openai import OpenAI
import pinecone
import uuid

# -------------------------
# Pinecone Setup (reuse your main.py settings)
# -------------------------
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp")
INDEX_NAME = "neuralic-memory"

# Initialize Pinecone
pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
index = pinecone.Index(INDEX_NAME)

# -------------------------
# OpenAI Setup
# -------------------------
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------------
# Store response in Pinecone
# -------------------------
def store_memory(user_id: str, text: str):
    emb_resp = openai_client.embeddings.create(
        model="text-embedding-3-large",
        input=text
    )
    vector = emb_resp.data[0].embedding
    vector_id = str(uuid.uuid4())
    index.upsert([(vector_id, vector, {"user_id": user_id, "text": text})])

# -------------------------
# Query memory for relevant past messages
# -------------------------
def query_memory(user_id: str, message: str, top_k: int = 3):
    emb_resp = openai_client.embeddings.create(
        model="text-embedding-3-large",
        input=message
    )
    query_vector = emb_resp.data[0].embedding
    result = index.query(vector=query_vector, top_k=top_k, include_metadata=True)
    
    relevant_texts = [
        match.metadata.get("text")
        for match in result.matches
        if match.metadata.get("user_id") == user_id
    ]
    return relevant_texts

# -------------------------
# Decision-making AI
# -------------------------
def decision_response(user_id: str, message: str):
    # Step 1: Check memory
    memory_matches = query_memory(user_id, message)
    if memory_matches:
        # Use the most recent memory match
        response = memory_matches[-1]
        return f"(From memory) {response}"

    # Step 2: If no relevant memory, call OpenAI GPT
    conversation = f"User: {message}\nAI:"
    try:
        completion = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": conversation}
            ],
            temperature=0.7,
            max_tokens=300
        )
        ai_reply = completion.choices[0].message['content'].strip()
    except Exception as e:
        ai_reply = f"Error generating response: {str(e)}"

    # Step 3: Store new AI response in memory
    store_memory(user_id, f"User: {message}")
    store_memory(user_id, f"AI: {ai_reply}")

    return ai_reply
