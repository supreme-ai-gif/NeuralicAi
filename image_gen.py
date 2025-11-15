
# image_gen.py
import os
import base64
from pathlib import Path
from openai import OpenAI
import asyncio
import uuid

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Folder to save generated images locally (temporary)
IMAGE_DIR = Path("static/images")
IMAGE_DIR.mkdir(exist_ok=True, parents=True)

async def generate_image(prompt):
    """
    Generate an image using OpenAI gpt-image-1 model.
    Returns a dict: {"base64":..., "url":...}
    """
    try:
        # Generate image
        resp = openai_client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="512x512",
            n=1
        )

        # Get URL from OpenAI
        url = resp.data[0].url

        # Download image and save locally to get URL and base64
        import requests
        img_data = requests.get(url).content
        filename = f"{uuid.uuid4().hex[:8]}.png"
        file_path = IMAGE_DIR / filename
        with open(file_path, "wb") as f:
            f.write(img_data)

        # Encode base64
        with open(file_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")

        # Return both hosted URL (on Render) and base64
        hosted_url = f"/static/images/{filename}"
        return {"base64": b64, "url": hosted_url}

    except Exception as e:
        print("Image generation error:", e)
        return {"error": str(e)}
