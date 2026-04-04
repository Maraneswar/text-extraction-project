import requests
import json
import sys
import os

BASE_URL = "http://127.0.0.1:7860"
API_KEY = "alldocex-test-key-2024"

def test_sync_extract(file_path):
    print(f"Testing synchronous extraction for: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return

    url = f"{BASE_URL}/api/v1/extract"
    headers = {
        "x-api-key": API_KEY
    }
    
    files = {
        "file": (os.path.basename(file_path), open(file_path, "rb"), "application/octet-stream")
    }
    
    try:
        response = requests.post(url, headers=headers, files=files)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n--- RESULTS ---")
            print(f"Filename: {result.get('filename')}")
            print(f"Status: {result.get('status')}")
            print(f"Extraction Success: {result.get('extraction', {}).get('success')}")
            
            text = result.get('extraction', {}).get('raw_text', '')
            print(f"Full Text Length: {len(text)}")
            print(f"Snippet: {text[:200]}...")
            
            summary = result.get('summary', {}).get('summary', '')
            if summary:
                print(f"Summary Snippet: {summary[:200]}...")
            
            entities = result.get('entities', {}).get('total_entities', 0)
            print(f"Total Entities Foundations: {entities}")
            
            print("\n[SUCCESS] Synchronous endpoint working correctly.")
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    # Test with the existing sample document
    sample_doc = "test_document.docx"
    test_sync_extract(sample_doc)
