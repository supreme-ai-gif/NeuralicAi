# main.py
import os
import base64
from fastapi import FastAPI, Request, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from ai import ask_text, start_autonomous, stop_autonomous
from image_gen import generate_image
from audio import save_b64_audio, transcribe_file, text_to_speech
from utils import verify_api_key

app = FastAPI(title="Neuralic AI Server")

# CORS (allow all for now)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ---------------------
# API Key verification
# ---------------------
async def check_key(request: Request):
    key = request.headers.get("x-api-key")
    if not key or not verify_api_key(key):
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return True

# ---------------------
# Chat endpoint
# ---------------------
@app.post("/chat")
async def chat_endpoint(request: Request):
    await check_key(request)
    data = await request.json()
    user_id = data.get("user_id")
    message = data.get("message")
    if not user_id or not message:
        return JSONResponse({"error": "user_id and message required"}, status_code=400)

    reply = await ask_text(user_id, message)
    return {"reply": reply}

# ---------------------
# Image generation endpoint
# ---------------------
@app.post("/image")
async def image_endpoint(request: Request):
    await check_key(request)
    data = await request.json()
    prompt = data.get("prompt")
    user_id = data.get("user_id")
    if not prompt or not user_id:
        return JSONResponse({"error": "prompt and user_id required"}, status_code=400)
    
    img = await generate_image(prompt)
    return img  # returns {"base64":..., "url":...}

# ---------------------
# Voice upload endpoint
# ---------------------
@app.post("/voice_upload")
async def voice_endpoint(request: Request):
    await check_key(request)
    data = await request.json()
    user_id = data.get("user_id")
    b64_audio = data.get("audio_base64")
    if not user_id or not b64_audio:
        return JSONResponse({"error": "user_id and audio_base64 required"}, status_code=400)

    path = save_b64_audio(b64_audio)
    text = transcribe_file(path)
    reply = await ask_text(user_id, text)
    
    # Generate TTS for reply
    tts_fname, tts_path = text_to_speech(reply)
    if tts_fname:
        with open(tts_path, "rb") as f:
            tts_b64 = base64.b64encode(f.read()).decode("utf-8")
    else:
        tts_b64 = ""

    return {"transcribed": text, "reply": reply, "tts_base64": tts_b64}

# ---------------------
# Autonomous start/stop
# ---------------------
@app.post("/autonomous_start")
async def autonomous_start(request: Request):
    await check_key(request)
    data = await request.json()
    user_id = data.get("user_id")
    if not user_id:
        return JSONResponse({"error": "user_id required"}, status_code=400)
    started = start_autonomous(user_id)
    return {"status": "started" if started else "already running"}

@app.post("/autonomous_stop")
async def autonomous_stop(request: Request):
    await check_key(request)
    data = await request.json()
    user_id = data.get("user_id")
    if not user_id:
        return JSONResponse({"error": "user_id required"}, status_code=400)
    stopped = stop_autonomous(user_id)
    return {"status": "stopped" if stopped else "not running"}

# ---------------------
# Root endpoint
# ---------------------
@app.get("/")
async def root():
    return {"message": "Neuralic AI Server is running"}

# At the very bottom of main.py

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
