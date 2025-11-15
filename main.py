# main.py
import os
from flask import Flask, request, jsonify
from openai import OpenAI
from memory import MemoryDB  # Your updated memory file

app = Flask(__name__)

# -----------------------------------
# ENVIRONMENT VARIABLES
# -----------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise Exception("Missing OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

memory = MemoryDB()


# -----------------------------------
# ROUTES
# -----------------------------------

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "AI server is running!"})


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_id = data.get("user_id", "default_user")
    user_message = data.get("message", "")

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    # -------------------------
    # 1. Search memory
    # -------------------------
    memories = memory.query(user_message)

    memory_texts = []
    for m in memories:
        if "metadata" in m and "text" in m['metadata']:
            memory_texts.append(m['metadata']['text'])

    memory_context = "\n".join(memory_texts) if memory_texts else "No memory found."

    # -------------------------
    # 2. Send to GPT-4o
    # -------------------------
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful AI assistant with memory."},
            {"role": "system", "content": f"Relevant memories:\n{memory_context}"},
            {"role": "user", "content": user_message}
        ]
    )

    ai_reply = response.choices[0].message["content"]

    # -------------------------
    # 3. Store new memory
    # -------------------------
    memory.store(user_id, f"user: {user_message}")
    memory.store(user_id, f"assistant: {ai_reply}")

    return jsonify({
        "reply": ai_reply,
        "memories_used": memory_texts
    })


# -----------------------------------
# START SERVER ON RENDER
# -----------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
