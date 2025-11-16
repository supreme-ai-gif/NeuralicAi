# audio_utils.py (or update your existing voice functions)
import base64
import requests
from fastapi import UploadFile
from decision_maker import make_decision

ELEVENLABS_API_KEY = "YOUR_ELEVENLABS_KEY"   # Or get from env
ELEVENLABS_VOICE_ID = "wDsJlOXPqcvIUKdLXjDs"  # Your Jarvis-like voice ID

def process_voice(user_id: str, file: UploadFile):
    """
    Receives voice file, converts to text (simulated),
    passes to decision maker, returns AI reply + audio base64.
    """

    # Step 1: Read user audio
    audio_bytes = file.file.read()
    user_text = f"Simulated transcription of user audio by {user_id}"

    # Step 2: Use decision_maker to generate reply
    ai_reply = make_decision(user_id, user_text)

    # Step 3: Convert AI reply to speech using ElevenLabs
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
        audio_base64 = base64.b64encode(b"tts_error").decode()
    else:
        audio_base64 = base64.b64encode(response.content).decode()

    return ai_reply, audio_base64
