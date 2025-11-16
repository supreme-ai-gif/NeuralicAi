import base64
import requests
from fastapi import UploadFile
from chat_logic import process_chat  # import your chat processor

ELEVENLABS_API_KEY = "your_api_key_here"
ELEVENLABS_VOICE_ID = "wDsJlOXPqcvIUKdLXjDs"

def process_voice(user_id: str, file: UploadFile):
    # Read user audio
    audio_bytes = file.file.read()

    # Simulate STT for now
    user_text = f"Simulated transcription of user audio by {user_id}"

    # Generate AI reply
    ai_reply = process_chat(user_id, user_text)

    # TTS with ElevenLabs
    tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
    payload = {"text": ai_reply, "voice_settings": {"stability": 0.75, "similarity_boost": 0.75}}
    response = requests.post(tts_url, json=payload)

    audio_base64 = base64.b64encode(response.content).decode() if response.status_code == 200 else base64.b64encode(b"tts_error").decode()

    return ai_reply, audio_base64
