# main.py
import os
import json
import base64
from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

# =====================================================
# Utility: Developer API Key Storage (dev_keys.json)
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
# Pinecone Memory Integration (Pinecone v2 FIXED)
# =====================================================
from pinecone import Pinecone, ServerlessSpec

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "neuralic-memory"

# Create client
pc = Pinecone(api_key=PINECONE_API_KEY)

# Get list of indexes
existing_indexes = [idx["name"] for idx in pc.list_indexes()]

# Create index if missing
if INDEX_NAME not in existing_indexes:
    pc.create_index(
        name=INDEX_NAME,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )

# Connect to index
index = pc.Index(name=INDEX_NAME)



    # Image Generation with OpenAI DALL·E
# =====================================================
import openai
import base64
import os

openai.api_key = os.getenv("OPENAI_API_KEY")  # Make sure your key is set in Render

def generate_image(prompt: str):
    """
    Generate an image from prompt using OpenAI DALL·E API
    and return a base64 string and a URL path for static serving.
    """

    try:
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="512x512"
        )
        # Image returned as base64
        image_base64 = response['data'][0]['b64_json']
        # Optional: save image to static folder
        image_bytes = base64.b64decode(image_base64)
        filename = f"{prompt.replace(' ', '_')}.png"
        static_path = os.path.join("static", "images")
        os.makedirs(static_path, exist_ok=True)
        file_path = os.path.join(static_path, filename)
        with open(file_path, "wb") as f:
            f.write(image_bytes)

        url = f"/static/images/{filename}"
        return url, image_base64

    except Exception as e:
        # Fallback if API fails
        fallback = base64.b64encode(b"image_error").decode()
        return "/static/images/error.png", fallback

# =====================================================
# Voice Processing with ElevenLabs
# =====================================================
import requests
import base64
from fastapi import UploadFile

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")  # Set in Render
ELEVENLABS_VOICE_ID = "wDsJlOXPqcvIUKdLXjDs"       # Example voice ID

def process_voice(user_id: str, file: UploadFile):
    """
    Convert uploaded user voice to text (optional STT),
    then generate AI response and return TTS audio as base64.
    """

    # --- Step 1: Read user audio ---
    audio_bytes = file.file.read()

    # Optional: You can integrate STT here using OpenAI Whisper API
    # For now, we simulate user message text
    user_text = f"Simulated transcription of user audio by {user_id}"

    # --- Step 2: AI generates response ---
    from main import process_chat  # Use your GPT chat logic
    ai_reply = process_chat(user_id, user_text)

    # --- Step 3: Convert AI reply to speech using ElevenLabs ---
    tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": ai_reply,
        "voice_settings": {"stability": 0.75, "similarity_boost": 0.75}
    }

    response = requests.post(tts_url, json=payload)
    if response.status_code != 200:
        # Fallback if TTS fails
        audio_base64 = base64.b64encode(b"tts_error").decode()
    else:
        audio_base64 = base64.b64encode(response.content).decode()

    return ai_reply, audio_base64

# =====================================================
# Chat Logic (GPT-powered)
# =====================================================
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")  # Make sure your key is set in Render

def process_chat(user_id: str, message: str):
    """
    Processes a chat message using OpenAI GPT-4 and stores the conversation in memory.
    """
    # Store user message in memory
    store_memory(user_id, f"User: {message}")

    # Prepare conversation history
    history = get_memory(user_id)
    conversation = "\n".join(history) + f"\nAI:"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": conversation}
            ],
            temperature=0.7,
            max_tokens=300
        )
        ai_reply = response.choices[0].message['content'].strip()
    except Exception as e:
        ai_reply = f"Error: {str(e)}"

    # Store AI reply in memory
    store_memory(user_id, f"AI: {ai_reply}")

    return ai_reply
# =====================================================
# FastAPI Setup with CORS
# =====================================================
app = FastAPI(title="Neuralic AI Full Server")

# -----------------------------
# CORS Middleware
# -----------------------------
# Replace with your frontend URL(s). For local dev:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates AFTER CORS
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

MASTER_PASSWORD = os.getenv("MASTER_PASSWORD", "supersecretpassword")

# =====================================================
# ADMIN ENDPOINTS
# =====================================================
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

# =====================================================
# AI ENDPOINTS
# =====================================================
@app.post("/chat")
async def chat_endpoint(
    user_id: str = Form(...),
    message: str = Form(...),
    api_key: str = Form(...)
):
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
async def voice_endpoint(
    user_id: str = Form(...),
    file: UploadFile = File(...),
    api_key: str = Form(...)
):
    if not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")

    text_response, audio_base64 = process_voice(user_id, file)
    return {"reply": text_response, "audio": audio_base64}

# =====================================================
# FRONTEND (Dashboard)
# =====================================================
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# =====================================================
# Run Server (python main.py)
# =====================================================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
