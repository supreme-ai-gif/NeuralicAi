# decision_maker.py
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")  # Ensure this is set in Render

def make_decision(user_input: str, memory: list):
    """
    Uses GPT to decide the AI's next action based on user input and memory.
    
    Parameters:
        user_input (str): Latest message from the user.
        memory (list): List of previous messages for context.
    
    Returns:
        dict: Contains 'action' and 'message' keys.
    """

    # Build conversation context for GPT
    conversation = "\n".join(memory) + f"\nUser: {user_input}\nAI:"

    # Define system instructions for decision making
    system_prompt = (
        "You are an autonomous AI assistant that decides the best action "
        "based on user input and context. Choose one action type from: "
        "assist, fun, warn, redirect, default. "
        "Return the action and a concise message for the user."
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": conversation}
            ],
            temperature=0.7,
            max_tokens=100
        )
        # GPT returns a text like: {"action": "assist", "message": "I will help you with that."}
        # Try to parse it as JSON
        import json
        content = response.choices[0].message['content'].strip()
        decision = json.loads(content)
        # Ensure required keys
        if "action" not in decision or "message" not in decision:
            decision = {"action": "default", "message": content}

    except Exception as e:
        # Fallback if GPT fails
        decision = {"action": "default", "message": f"Error deciding: {str(e)}"}

    return decision
