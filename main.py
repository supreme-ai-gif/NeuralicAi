# main.py
import os
import json
import base64
import requests
from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import openai
from pinecone import Pinecone, ServerlessSpec
from decision_maker import make_decision  # Your decision logic

# =====================================================
# Constants and environment
# =====================================================
PORT = int(os.getenv("PORT", 10000))
MASTER_PASSWORD = os.getenv("MASTER_PASSWORD", "supersecretpassword")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "wDsJlOXPqcvIUKdLXjDs")

# OpenAI client
openai.api_key = OPENAI_API_KEY

# =====================================================
# Utility: Developer API Key Storage
# =====================================================
DEV_KEYS_FILE = "dev_keys.json"
if not os.path.exists(DEV_KEYS_FILE):
    with open(DEV_KEYS_FILE, "w") as f:
        json.dump([], f)

def load_keys():
    with open(DEV_KEYS_FILE, "r") as f:
        return json.load(f)

def save_keys(keys):
    with open(DEV_KEYS_FILE, "w") as f:
        json.dump(keys, f, indent=4)

def create_api_key(owner_name: str):
    import uuid
    key = str(uuid.uuid4())
    keys = load_keys()
    keys.append({"owner": owner_name, "key": key})
    save_keys(keys)
    return key

def list_keys():
    return load_keys()

def revoke_key(key: str):
    keys = load_keys()
    new_keys = [k for k in keys if k["key"] != key]
    save_keys(new_keys)
    return len(keys) != len(new_keys)

def verify_api_key(key: str):
    keys = load_keys()
    return any(k["key"] == key for k in keys)

# =====================================================
# Pinecone Memory Integration (v2)
# =====================================================
INDEX_NAME = "neuralic-memory"
pc = Pinecone(api_key=PINECONE_API_KEY)

# Create index if missing
existing_indexes = pc.list_indexes()
if INDEX_NAME not in existing_indexes:
    pc.create_index(
        name=INDEX_NAME,
        dimension=1536,
        metric='cosine',
        spec=ServerlessSpec(cloud='aws', region='us-east-1')
    )

# Connect to index
index = pc.Index(name=INDEX_NAME)

# -------------------------------
# Memory store/retrieve
# -------------------------------
def store_memory(user_id: str, text: str):
    """Convert text to embeddings and store in Pinecone."""
    emb_resp = openai.Embedding.create(
        model="text-embedding-3-large",
        input=text
    )
    vector = emb_resp.data[0].embedding
    import uuid
    vector_id = str(uuid.uuid4())
    index.upsert([(vector_id, vector, {"user_id": user_id, "text": text})])

def get_memory(user_id: str, top_k: int = 5):
    """Retrieve top_k relevant messages from Pinecone."""
    query_text = f"Retrieve conversation for {user_id}"
    emb_resp = openai.Embedding.create(
        model="text-embedding-3-large",
        input=query_text
    )
    query_vector = emb_resp.data[0].embedding
    result = index.query(vector=query_vector, top_k=top_k, include_metadata=True)
    memory = [match.metadata.get("text") for match in result.matches if match.metadata.get("user_id")==user_id]
    return memory

# =====================================================
# Image Generation
# =====================================================
def generate_image(prompt: str):
    try:
        response = openai.Image.create(prompt=prompt, n=1, size="512x512")
        image_base64 = response['data'][0]['b64_json']
        filename = f"{prompt.replace(' ','_')}.png"
        static_path = os.path.join("static","images")
        os.makedirs(static_path, exist_ok=True)
        with open(os.path.join(static_path, filename),"wb") as f:
            f.write(base64.b64decode(image_base64))
        url = f"/static/images/{filename}"
        return url, image_base64
    except Exception:
        fallback = base64.b64encode(b"image_error").decode()
        return "/static/images/error.png", fallback

# =====================================================
# Voice Processing
# =====================================================
def process_voice(user_id: str, file: UploadFile):
    audio_bytes = file.file.read()
    user_text = f"Simulated transcription of user audio by {user_id}"
    ai_reply = process_chat(user_id, user_text)
    tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type":"application/json"}
    payload = {"text": ai_reply,"voice_settings":{"stability":0.75,"similarity_boost":0.75}}
    response = requests.post(tts_url,json=payload)
    audio_base64 = base64.b64encode(response.content).decode() if response.status_code==200 else base64.b64encode(b"tts_error").decode()
    return ai_reply, audio_base64

# =====================================================
# Chat Logic
# =====================================================
def process_chat(user_id: str, message: str):
    store_memory(user_id, f"User: {message}")
    history = get_memory(user_id)
    conversation = "\n".join(history) + "\nAI:"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role":"system","content":"You are a helpful AI assistant."},
                {"role":"user","content":conversation}
            ],
            temperature=0.7,
            max_tokens=300
        )
        ai_reply = response.choices[0].message['content'].strip()
    except Exception as e:
        ai_reply = f"Error: {str(e)}"
    store_memory(user_id, f"AI: {ai_reply}")
    return ai_reply

# =====================================================
# FastAPI App Setup
# =====================================================
app = FastAPI(title="Neuralic AI Full Server")

# CORS Middleware - allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to admin URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# =====================================================
# Admin Endpoints
# =====================================================
@app.post("/admin/create_key")
async def admin_create_key(owner: str = Form(...), password: str = Form(...)):
    if password != MASTER_PASSWORD:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"success": True, "key": create_api_key(owner)}

@app.get("/admin/list_keys")
async def admin_list_keys(password: str):
    if password != MASTER_PASSWORD:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"keys": list_keys()}

@app.post("/admin/revoke_key")
async def admin_revoke_key(key: str = Form(...), password: str = Form(...)):
    if password != MASTER_PASSWORD:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"success": revoke_key(key)}

# =====================================================
# AI Endpoints
# =====================================================
@app.post("/chat")
async def chat_endpoint(user_id: str = Form(...), message: str = Form(...), api_key: str = Form(...)):
    if not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return {"reply": process_chat(user_id, message)}

@app.post("/image")
async def image_endpoint(prompt: str = Form(...), api_key: str = Form(...)):
    if not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    url, base64_img = generate_image(prompt)
    return {"url": url, "base64": base64_img}

@app.post("/voice_upload")
async def voice_endpoint(user_id: str = Form(...), file: UploadFile = File(...), api_key: str = Form(...)):
    if not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    reply, audio_base64 = process_voice(user_id, file)
    return {"reply": reply, "audio": audio_base64}

# =====================================================
# Decision-making endpoint
# =====================================================
@app.post("/decision")
async def decision_endpoint(user_id: str = Form(...), message: str = Form(...), api_key: str = Form(...)):
    if not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    reply = make_decision(user_id, message)  # your decision_maker logic
    return {"reply": reply}

# =====================================================
# Frontend
# =====================================================
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# =====================================================
# Run server
# =====================================================
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
