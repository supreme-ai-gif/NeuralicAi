# ai.py
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

class NeuralicAI:
    def __init__(self):
        self.text_model = "gpt-4o"
        self.realtime_model = "gpt-4o-realtime-preview"

    async def ask_text(self, user_id, message):
        response = openai.ChatCompletion.create(
            model=self.text_model,
            messages=[{"role": "user", "content": message}]
        )
        return response.choices[0].message["content"]

    async def start_realtime_session(self):
        self.session = openai.realtime.sessions.create(
            model=self.realtime_model
        )
        return self.session

    async def process_realtime(self):
        events = openai.realtime.sessions.receive(self.session.id)
        processed = []

        for e in events:
            if e.type == "response.output_text.delta":
                processed.append({"type": "message", "data": e.delta})

            if e.type == "response.output_audio.delta":
                processed.append({"type": "audio", "data": e.delta})

            if e.type == "response.function_call":
                processed.append({
                    "type": "action",
                    "name": e.name,
                    "arguments": e.arguments
                })

        return processed

    def add_user_message(self, text):
        openai.realtime.messages.create(
            session_id=self.session.id,
            role="user",
            content=text
        )
