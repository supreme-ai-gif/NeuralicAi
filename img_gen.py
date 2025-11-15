# image_gen.py
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

async def generate_image(prompt):
    img = openai.images.generate(
        prompt=prompt,
        model="gpt-image-1"
    )
    return img.data[0].url
