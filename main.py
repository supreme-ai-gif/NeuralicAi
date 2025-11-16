# main.py
import os
import json
import base64
import uuid
import requests
from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from decision_maker import make_decision
import uvicorn
import openai
import pinecone

# =====================================================
# CONFIGURATION
# =====================================================
PORT = int(os.getenv("PORT", 10000))
MASTER_PASSWORD = os.getenv("MASTER_PASSWORD", "supersecretpassword")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp")
INDEX_NAME = "neuralic-memory"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "wDsJlOXPqcvIUKdLXjDs")  # your voice ID

# =====================================================
# FASTAPI APP
# =====================================================
app = FastAPI(title="Neuralic AI Full Server")

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# =====================================================
# DEV API KEY STORAGE
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
# PINECONE MEMORY
# =====================================================
pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)

if INDEX_NAME not in pinecone.list_indexes():
    pinecone.create_index(name=INDEX_NAME, dimension=1536, metric="cosine")

index = pinecone.Index(INDEX_NAME)

openai.api_key = OPENAI_API_KEY

def store_memory(user_id: str, text: str):
    emb_resp = openai.Embedding.create(model="text-embedding-3-large", input=text)
    vector = emb_resp.data[0].embedding
    vector_id = str(uuid.uuid4())
    index.upsert([(vector_id, vector, {"user_id": user_id, "text": text})])

def get_memory(user_id: str, top_k: int = 5):
    query_text = f"Retrieve conversation for {user_id}"
    emb_resp = openai.Embedding.create(model="text-embedding-3-large", input=query_text)
    query_vector = emb_resp.data[0].embedding
    result = index.query(vector=query_vector, top_k=top_k, include_metadata=True)
    memory = [match.metadata["text"] for match in result.matches if match.metadata.get("user_id") == user_id]
    return memory

# =====================================================
# IMAGE GENERATION
# =====================================================
def generate_image(prompt: str):
    try:
        response = openai.Image.create(prompt=prompt, n=1, size="512x512")
        image_base64 = response['data'][0]['b64_json']
        image_bytes = base64.b64decode(image_base64)
        filename = f"{prompt.replace(' ', '_')}.png"
        path = os.path.join("static", "images")
        os.makedirs(path, exist_ok=True)
        file_path = os.path.join(path, filename)
        with open(file_path, "wb") as f:
            f.write(image_bytes)
        url = f"/static/images/{filename}"
        return url, image_base64
    except:
        fallback = base64.b64encode(b"image_error").decode()
        return "/static/images/error.png", fallback

# =====================================================
# VOICE PROCESSING
# =====================================================
def process_voice(user_id: str, file: UploadFile):
    audio_bytes = file.file.read()
    user_text = f"Simulated transcription of user audio by {user_id}"
    ai_reply = process_chat(user_id, user_text)
    tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
    payload = {"text": ai_reply, "voice_settings": {"stability":0.75, "similarity_boost":0.75}}
    response = requests.post(tts_url, json=payload)
    audio_base64 = base64.b64encode(response.content).decode() if response.status_code==200 else base64.b64encode(b"tts_error").decode()
    return ai_reply, audio_base64

# =====================================================
# CHAT LOGIC
# =====================================================
def process_chat(user_id: str, message: str):
    store_memory(user_id, f"User: {message}")
    history = get_memory(user_id)
    conversation = "\n".join(history) + "\nAI:"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role":"system","content":"You are a helpful AI assistant."},
                      {"role":"user","content":conversation}],
            temperature=0.7,
            max_tokens=300
        )
        ai_reply = response.choices[0].message['content'].strip()
    except Exception as e:
        ai_reply = f"Error: {str(e)}"
    store_memory(user_id, f"AI: {ai_reply}")
    return ai_reply

# =====================================================
# ADMIN ENDPOINTS
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
# AI ENDPOINTS
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
from decision_maker import make_decision

@app.post("/decision")
async def decision_endpoint(
    user_id: str = Form(...),
    message: str = Form(...),
    api_key: str = Form(...)
):
    if not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")

    reply = decision_response(user_id, message)
    return {"reply": reply}
    
# =====================================================
# FRONTEND
# =====================================================
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# =====================================================
# RUN SERVER
# =====================================================
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
