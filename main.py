from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import os

# Import modular files
from memory import store_memory, get_memory
from image_gen import generate_image
from voice import process_voice
from decision_maker import make_decision

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
