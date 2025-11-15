
# audio.py
import os
import base64
from pathlib import Path
from openai import OpenAI
import requests
import uuid

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Folder to save uploaded audio and TTS files
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)

def save_b64_audio(b64str, filename=None):
    """Save a base64 audio payload to file and return path."""
    if filename is None:
        filename = f"audio_{uuid.uuid4().hex[:8]}.mp3"
    path = UPLOAD_DIR / filename
    with open(path, "wb") as f:
        f.write(base64.b64decode(b64str))
    return str(path)

def transcribe_file(path, model="whisper-1"):
    """Transcribe audio file using OpenAI Whisper."""
    try:
        with open(path, "rb") as af:
            resp = openai_client.audio.transcriptions.create(model=model, file=af)
        return resp.text if hasattr(resp, "text") else resp.get("text", "")
    except Exception as e:
        print("Transcription error:", e)
        return ""

def tts_openai(text, voice="alloy"):
    """
    Generate TTS audio using OpenAI TTS.
    Returns (filename, path) or (None, None) if failed.
    """
    try:
        resp = openai_client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice=voice,
            input=text
        )
        filename = f"tts_{uuid.uuid4().hex[:8]}.mp3"
        path = UPLOAD_DIR / filename

        # Write TTS bytes to file
        data = resp if isinstance(resp, bytes) else resp.content
        with open(path, "wb") as f:
            f.write(data)

        return filename, str(path)
    except Exception as e:
        print("OpenAI TTS error:", e)
        return None, None

def tts_elevenlabs(text, voice="alloy"):
    """
    Fallback TTS using ElevenLabs.
    Requires ELEVENLABS_API_KEY environment variable.
    Returns (filename, path) or (None, None).
    """
    key = os.getenv("ELEVENLABS_API_KEY")
    if not key:
        return None, None
    try:
        url = "https://api.elevenlabs.io/v1/text-to-speech/EXAVITQu4vr4xnSDxMaL/stream"  # placeholder voice id
        headers = {"xi-api-key": key, "Content-Type": "application/json"}
        payload = {"text": text, "voice": voice}
        r = requests.post(url, json=payload, headers=headers, stream=True, timeout=30)
        if r.status_code == 200:
            filename = f"tts_eleven_{uuid.uuid4().hex[:8]}.mp3"
            path = UPLOAD_DIR / filename
            with open(path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return filename, str(path)
        else:
            print("ElevenLabs TTS error status:", r.status_code, r.text)
            return None, None
    except Exception as e:
        print("ElevenLabs TTS exception:", e)
        return None, None

def text_to_speech(text):
    """
    Try OpenAI TTS first; fallback to ElevenLabs.
    Returns (filename, path) or (None, None) if both fail.
    """
    fname, path = tts_openai(text)
    if fname:
        return fname, path
    return tts_elevenlabs(text)
