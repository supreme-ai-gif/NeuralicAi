from memory import get_memory, store_memory
from main import process_chat  # or GPT logic

def make_decision(user_id: str, message: str):
    # Step 1: Check memory
    history = get_memory(user_id)
    for msg in history[::-1]:  # check recent messages first
        if message.lower() in msg.lower():
            return msg  # return stored answer

    # Step 2: Fallback to GPT
    ai_reply = process_chat(user_id, message)
    store_memory(user_id, f"AI: {ai_reply}")
    return ai_reply
