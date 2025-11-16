import os
from fastapi import FastAPI, Form, UploadFile, Request, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from dev_keys import create_api_key, list_keys, revoke_key, verify_api_key
import uvicorn

# Import modules
from audio_utils import process_voice
from image_gen import generate_image
from memory import store_memory, get_memory
from decision_maker import make_decision
from chat_logic import process_chat  # define your GPT chat logic here

# FastAPI setup
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True, 
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


MASTER_PASSWORD = "supersecretpassword"

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

# AI endpoints
@app.post("/chat")
async def chat_endpoint(user_id: str = Form(...), message: str = Form(...), api_key: str = Form(...)):
    from api_keys import verify_api_key
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
async def voice_endpoint(
    user_id: str = Form(...),
    file: UploadFile = File(...),
    api_key: str = Form(...)
):
    if not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")

    reply, audio_base64 = process_voice(user_id, file)
    return {"reply": reply, "audio": audio_base64}

@app.post("/decision")
async def decision_endpoint(user_id: str = Form(...),
                            message: str = Form(...),
                            api_key: str = Form(...)):
    if not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")

    reply = make_decision(user_id, message)
    return {"reply": reply}

# Fronted 
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 10000)), reload=True)
