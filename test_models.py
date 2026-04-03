import os
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

for model_name in ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-2.5-flash", "gemini-pro"]:
    try:
        print(f"Testing {model_name}...")
        model = genai.GenerativeModel(model_name)
        img = Image.new('RGB', (100, 100), color = 'white')
        response = model.generate_content(["What color is this?", img])
        print(f"{model_name} Success!")
    except Exception as e:
        print(f"{model_name} Failed: {type(e).__name__}")
