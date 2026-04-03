import config
import google.generativeai as genai

genai.configure(api_key=config.GEMINI_API_KEY)
models = [m.name for m in genai.list_models()]
print("Available models:")
for m in models:
    if 'flash' in m.lower() or '2.5' in m.lower() or '1.5' in m.lower():
        print(m)
