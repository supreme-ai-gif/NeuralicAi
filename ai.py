# ai.py
import os
import json
import asyncio
from openai import OpenAI
from memory import MemoryDB
from image_gen import generate_image
from audio import text_to_speech
import uuid

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
memory = MemoryDB()

CHAT_MODEL = "gpt-4o"
SYSTEM_PROMPT = (
    "You are Neuralic AI. You can answer normally, or when asked to plan or act, "
    "emit JSON in the following format (no extra text):\n"
    '{"action": "speak"|"generate_image"|"remember"|"none", "content": "..."}\n'
    "When autonomous, pick an action and content. Keep JSON small and valid."
)

# ---------------------
# Text Chat
# ---------------------
async def ask_text(user_id, message, personality=None):
    """
    Ask AI a question and get a text reply.
    """
    # Retrieve relevant memory
    mems = memory.query(message)
    mem_texts = []
    for m in mems:
        md = getattr(m, "metadata", None) or m.get("metadata", {})
        if md and md.get("text"):
            mem_texts.append(md["text"])
    mem_context = "\n".join(mem_texts) if mem_texts else ""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": f"Relevant memories:\n{mem_context}"},
        {"role": "user", "content": message}
    ]

    resp = openai_client.chat.completions.create(
        model=CHAT_MODEL, 
        messages=messages, 
        temperature=0.7
    )
    text = resp.choices[0].message["content"]
    # Store AI reply in memory
    memory.store(user_id, f"assistant: {text}")
    return text

# ---------------------
# Autonomous Decision-Making
# ---------------------
async def decide_action(user_id, context=""):
    """
    Ask AI to decide an action in JSON format.
    """
    prompt = f"User: {user_id}\nContext: {context}\nDecide one action and respond only with JSON."
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]
    resp = openai_client.chat.completions.create(
        model=CHAT_MODEL, 
        messages=messages, 
        temperature=0.9, 
        max_tokens=300
    )
    txt = resp.choices[0].message["content"].strip()
    try:
        start = txt.find("{")
        end = txt.rfind("}") + 1
        j = txt[start:end]
        action = json.loads(j)
        return action
    except Exception as e:
        print("Action parse error:", e, "raw:", txt)
        return {"action": "none", "content": ""}

# ---------------------
# Autonomous Loop
# ---------------------
_autonomous_tasks = {}  # user_id -> asyncio.Task

async def _run_autonomous_loop(user_id, interval=30):
    """
    Run autonomous actions every `interval` seconds.
    """
    while True:
        context = "Autonomous thinking"
        action = await decide_action(user_id, context)

        if action["action"] == "speak" and action.get("content"):
            # Store memory and create TTS
            memory.store(user_id, f"AI (autonomous): {action['content']}")
            fname, path = text_to_speech(action["content"])
            print(f"[Autonomous] speak: {action['content']} -> {fname}")

        elif action["action"] == "generate_image" and action.get("content"):
            # Generate image asynchronously
            img = await generate_image(action["content"])
            memory.store(user_id, f"AI generated image: {action['content']} -> {img['url']}")
            print(f"[Autonomous] image: {img['url']}")

        elif action["action"] == "remember" and action.get("content"):
            memory.store(user_id, action["content"])
            print(f"[Autonomous] remembered: {action['content']}")

        # else do nothing
        await asyncio.sleep(interval)

# ---------------------
# Start/Stop Autonomous
# ---------------------
def start_autonomous(user_id, interval=30):
    """
    Start autonomous loop for a user.
    """
    if user_id in _autonomous_tasks:
        return False
    loop = asyncio.get_event_loop()
    task = loop.create_task(_run_autonomous_loop(user_id, interval))
    _autonomous_tasks[user_id] = task
    return True

def stop_autonomous(user_id):
    """
    Stop autonomous loop for a user.
    """
    task = _autonomous_tasks.pop(user_id, None)
    if task:
        task.cancel()
        return True
    return False
