import os
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

print(f"API Key available: {bool(api_key)}")
print(f"Model: {model_name}")

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    # create a dummy image
    img = Image.new('RGB', (100, 100), color = 'white')
    response = model.generate_content(["What color is this?", img])
    print("Success:", response.text)
except Exception as e:
    import traceback
    traceback.print_exc()
