# decision_maker.py
from memory import store_memory, get_memory
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def make_decision(user_id: str, message: str, memory_top_k: int = 5):
    """
    Decision-making function:
    1. Checks memory first.
    2. If no relevant memory, asks GPT.
    3. Stores the result in memory.
    """

    # ------------------------------
    # Step 1: Check memory
    # ------------------------------
    memory_history = get_memory(user_id, top_k=memory_top_k)
    relevant = None
    for mem in memory_history[::-1]:  # Check recent first
        if message.lower() in mem.lower():
            relevant = mem
            break

    if relevant:
        # Memory contains a related answer
        reply = f"Memory recall: {relevant}"
    else:
        # ------------------------------
        # Step 2: Ask GPT
        # ------------------------------
        conversation = "\n".join(memory_history) + f"\nUser: {message}\nAI:"
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant."},
                    {"role": "user", "content": conversation}
                ],
                temperature=0.7,
                max_tokens=300
            )
            reply = response.choices[0].message['content'].strip()
        except Exception as e:
            reply = f"Error: {str(e)}"

        # ------------------------------
        # Step 3: Store reply in memory
        # ------------------------------
        store_memory(user_id, f"User: {message}")
        store_memory(user_id, f"AI: {reply}")

    return reply
