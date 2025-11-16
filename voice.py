import base64
import requests
from fastapi import UploadFile
from main import process_chat  # Import chat logic

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "wDsJlOXPqcvIUKdLXjDs")

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
