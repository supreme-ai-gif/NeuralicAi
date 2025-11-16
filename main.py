from fastapi import FastAPI, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi import Request
import uvicorn

# ----------------------------
# IMPORT YOUR MODULES
# ----------------------------
from memory import store_memory, get_memory
from decision_maker import make_decision
from audio_utils import process_voice
from image_gen import generate_image

# ----------------------------
# INIT APP
# ----------------------------
app = FastAPI(title="Neuralic AI Server")

# ----------------------------
# ENABLE CORS FOR ALL ORIGINS
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # allow any frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
templates = Jinja2Templates(directory="templates"
                            
# ----------------------------
# SIMPLE CHAT ENDPOINT
# ----------------------------
@app.post("/chat")
async def chat_endpoint(
    user_id: str = Form(...),
    message: str = Form(...)
):
    store_memory(user_id, f"User: {message}")
    ai_reply = make_decision(user_id, message)
    store_memory(user_id, f"AI: {ai_reply}")
    return {"reply": ai_reply}

# ----------------------------
# DECISION MAKER ENDPOINT
# ----------------------------
@app.post("/decision")
async def decision_endpoint(
    user_id: str = Form(...),
    message: str = Form(...)
):
    reply = make_decision(user_id, message)
    return {"reply": reply}

# ----------------------------
# VOICE ENDPOINT
# ----------------------------
@app.post("/voice")
async def voice_endpoint(
    user_id: str = Form(...),
    file: UploadFile = File(...)
):
    reply, audio_b64 = process_voice(user_id, file)
    return {"reply": reply, "audio": audio_b64}

# ----------------------------
# IMAGE ENDPOINT
# ----------------------------
@app.post("/image")
async def image_endpoint(prompt: str = Form(...)):
    url, base64_img = generate_image(prompt)
    return {"url": url, "base64": base64_img}

# ----------------------------
# BASIC HOMEPAGE
# ----------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
# ----------------------------
# RUN SERVER
# ----------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10000, reload=True)
