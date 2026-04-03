import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

def test_api():
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": "Hello, world!"}]}]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        with open("clean_output.txt", "w", encoding="utf-8") as f:
            f.write(f"Status Code: {response.status_code}\n")
            f.write(json.dumps(response.json(), indent=2))
    except Exception as e:
        with open("clean_output.txt", "w", encoding="utf-8") as f:
            f.write(str(e))

test_api()
