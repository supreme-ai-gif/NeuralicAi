# image_gen.py
import os
import base64
import openai

# Make sure your OpenAI key is set as an environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")  

def generate_image(prompt: str):
    """
    Generates an image using OpenAI DALL·E.
    Returns:
        - URL to serve the image
        - base64 string of the image
    """
    try:
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="512x512"
        )
        # Get base64 image from OpenAI response
        image_base64 = response['data'][0]['b64_json']

        # Save image to static folder for frontend
        image_bytes = base64.b64decode(image_base64)
        filename = f"{prompt.replace(' ', '_')}.png"
        static_path = os.path.join("static", "images")
        os.makedirs(static_path, exist_ok=True)
        file_path = os.path.join(static_path, filename)

        with open(file_path, "wb") as f:
            f.write(image_bytes)

        url = f"/static/images/{filename}"
        return url, image_base64

    except Exception as e:
        # Fallback if API fails
        fallback_base64 = base64.b64encode(b"image_error").decode()
        return "/static/images/error.png", fallback_base64
