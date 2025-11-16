from memory import get_memory, store_memory
from chat_logic import process_chat  # reuse your GPT chat

def decision_response(user_id: str, message: str):
    # Check memory first
    memory = get_memory(user_id)
    if message in memory:
        return f"Memory answer: {memory[-1]}"
    
    # Else, ask GPT
    ai_reply = process_chat(user_id, message)
    store_memory(user_id, f"Decision: {ai_reply}")
    return ai_reply
