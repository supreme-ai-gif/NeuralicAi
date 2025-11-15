# main.py
import os
import json
import base64
from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn

# -------------------------------
# -------------------------------
# Utility functions (simulate utils.py)
# -------------------------------
# Dev keys storage
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

# -------------------------------
# -------------------------------
# Pinecone memory (simplified example)
# -------------------------------
# This is just a placeholder; replace with your real Pinecone logic
MEMORY_DB = {}

def store_memory(user_id, text):
    if user_id not in MEMORY_DB:
        MEMORY_DB[user_id] = []
    MEMORY_DB[user_id].append(text)

def get_memory(user_id):
    return MEMORY_DB.get(user_id, [])

# -------------------------------
# -------------------------------
# Image generation placeholder
# -------------------------------
def generate_image(prompt):
    # placeholder for real image generation (OpenAI or local model)
    base64_img = base64.b64encode(b"fakeimagebytes").decode()
    url = f"/static/images/{prompt.replace(' ','_')}.png"
    return url, base64_img

# -------------------------------
# -------------------------------
# Voice processing placeholder
# -------------------------------
def process_voice(user_id, file: UploadFile):
    audio_bytes = file.file.read()
    text_response = f"Simulated voice response for {user_id}"
    audio_base64 = base64.b64encode(audio_bytes).decode()
    return text_response, audio_base64

# -------------------------------
# -------------------------------
# Chat logic (simplified GPT placeholder)
# -------------------------------
def process_chat(user_id: str, message: str):
    store_memory(user_id, message)
    return f"Echo from AI for {user_id}: {message}"

# -------------------------------
# -------------------------------
# FastAPI app setup
# -------------------------------
app = FastAPI(title="Neuralic AI Full Server")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# -------------------------------
# Admin endpoints
# -------------------------------
MASTER_PASSWORD = os.getenv("MASTER_PASSWORD", "supersecretpassword")

@app.post("/admin/create_key")
async def admin_create_key(owner: str = Form(...), password: str = Form(...)):
    if password != MASTER_PASSWORD:
        raise HTTPException(status_code=401, detail="Unauthorized")
    key = create_api_key(owner)
    return {"success": True, "key": key}

@app.get("/admin/list_keys")
async def admin_list_keys(password: str):
    if password != MASTER_PASSWORD:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"keys": list_keys()}

@app.post("/admin/revoke_key")
async def admin_revoke_key(key: str = Form(...), password: str = Form(...)):
    if password != MASTER_PASSWORD:
        raise HTTPException(status_code=401, detail="Unauthorized")
    result = revoke_key(key)
    return {"success": result}

# -------------------------------
# AI endpoints
# -------------------------------
@app.post("/chat")
async def chat_endpoint(user_id: str = Form(...), message: str = Form(...), api_key: str = Form(...)):
    if not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    reply = process_chat(user_id, message)
    return {"reply": reply}

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
    text_response, audio_base64 = process_voice(user_id, file)
    return {"reply": text_response, "audio": audio_base64}

# -------------------------------
# Frontend dashboard placeholder
# -------------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# -------------------------------
# Run server
# -------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
