# chat_logic.py
from memory import store_memory, get_memory
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def process_chat(user_id: str, message: str):
    """
    Process a user message using OpenAI GPT and store conversation in memory.
    """
    # Store user message
    store_memory(user_id, f"User: {message}")

    # Retrieve conversation history
    history = get_memory(user_id)
    conversation = "\n".join(history) + "\nAI:"

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
        ai_reply = response.choices[0].message['content'].strip()
    except Exception as e:
        ai_reply = f"Error: {str(e)}"

    # Store AI reply
    store_memory(user_id, f"AI: {ai_reply}")

    return ai_reply
