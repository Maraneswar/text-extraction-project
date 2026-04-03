import config
import google.generativeai as genai
from PIL import Image

try:
    img = Image.new('RGB', (100, 100), color = 'white')
    genai.configure(api_key=config.GEMINI_API_KEY)
    
    for model_name in ["gemini-1.5-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash-8b"]:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(["Tell me what is in this image", img])
            print(f"SUCCESS with {model_name}:", response.text[:20])
            break
        except Exception as e:
            print(f"FAILED {model_name}: {type(e).__name__} {str(e)[:50]}")
except Exception as e:
    print("Fatal exception:", e)
