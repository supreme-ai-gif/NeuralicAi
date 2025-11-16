import openai
import base64
import os

openai.api_key = "YOUR_OPENAI_API_KEY"

def generate_image(prompt: str):
    try:
        response = openai.Image.create(prompt=prompt, n=1, size="512x512")
        image_base64 = response['data'][0]['b64_json']

        filename = f"{prompt.replace(' ', '_')}.png"
        static_path = os.path.join("static", "images")
        os.makedirs(static_path, exist_ok=True)
        file_path = os.path.join(static_path, filename)

        with open(file_path, "wb") as f:
            f.write(base64.b64decode(image_base64))

        url = f"/static/images/{filename}"
        return url, image_base64
    except Exception:
        fallback = base64.b64encode(b"image_error").decode()
        return "/static/images/error.png", fallback
