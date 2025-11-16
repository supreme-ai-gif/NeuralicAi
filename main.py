from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import os

# Import modular files
from memory import store_memory, get_memory
from image_gen import generate_image
from audio import process_voice
from decision_maker import make_decision

# Chat endpoint
@app.post("/chat")
async def chat_endpoint(user_id: str = Form(...), message: str = Form(...), api_key: str = Form(...)):
    if not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return {"reply": process_chat(user_id, message)}

# Image endpoint
@app.post("/image")
async def image_endpoint(prompt: str = Form(...), api_key: str = Form(...)):
    if not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    url, base64_img = generate_image(prompt)
    return {"url": url, "base64": base64_img}

# Voice endpoint
@app.post("/voice_upload")
async def voice_endpoint(user_id: str = Form(...), file: UploadFile = File(...), api_key: str = Form(...)):
    if not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    reply, audio_base64 = process_voice(user_id, file)
    return {"reply": reply, "audio": audio_base64}

# Decision-making endpoint
@app.post("/decision")
async def decision_endpoint(user_id: str = Form(...), message: str = Form(...), api_key: str = Form(...)):
    if not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    reply = make_decision(user_id, message)
    return {"reply": reply}

# Admin endpoints
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

app = FastAPI(title="Neuralic AI Full Server")

# CORS: allow all origins for now
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
MASTER_PASSWORD = os.getenv("MASTER_PASSWORD", "supersecretpassword")

# Admin endpoints, chat, image, voice, decision
# ... use previous endpoint definitions ...

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 10000)), reload=True)
