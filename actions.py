# actions.py
async def handle_ai_action(event):
    name = event["name"]
    args = event["arguments"]

    if name == "create_image":
        from image_gen import generate_image
        url = await generate_image(args["prompt"])
        return {"image_url": url}

    if name == "remember":
        return {"status": "stored"}

    return {"error": "unknown_action"}
