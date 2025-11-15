# main.py
import uvicorn
from fastapi import FastAPI, WebSocket, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from ai import NeuralicAI
from memory import MemoryDB
from image_gen import generate_image
from audio import decode_audio, encode_audio
from actions import handle_ai_action

app = FastAPI()
ai = NeuralicAI()
memory = MemoryDB()

# Allow any frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat")
async def chat_text(
    user_id: str = Form(...),
    message: str = Form(...)
):
    memory.store(user_id, message)
    reply = await ai.ask_text(user_id, message)
    memory.store(user_id, reply)
    return {"reply": reply}

@app.post("/image")
async def image(user_id: str = Form(...), prompt: str = Form(...)):
    img_url = await generate_image(prompt)
    memory.store(user_id, f"[IMAGE CREATED] {prompt}")
    return {"image_url": img_url}

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    session = await ai.start_realtime_session()

    try:
        while True:
            data = await ws.receive_bytes()

            audio_text = decode_audio(data)
            if audio_text:
                ai.add_user_message(audio_text)

                memory.store("voice-user", audio_text)

            ai_events = await ai.process_realtime()

            for event in ai_events:
                if event["type"] == "audio":
                    audio_chunk = encode_audio(event["data"])
                    await ws.send_bytes(audio_chunk)

                elif event["type"] == "message":
                    memory.store("voice-ai", event["data"])
                    await ws.send_json({"reply": event["data"]})

                elif event["type"] == "action":
                    result = await handle_ai_action(event)
                    await ws.send_json({"action_result": result})

    except Exception:
        await ws.close()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10000)
