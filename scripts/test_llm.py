import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

api_keys = os.getenv("OPENROUTER_API_KEYS", "").split(",")
model = os.getenv("OPENROUTER_MODEL", "google/gemini-flash-1.5-exp:free")

def test_key(key):
    key = key.strip()
    if not key: return False
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "X-Title": "QuizSensei-Test"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Hello, please reply with exactly the word 'SUCCESS' if you are working."}],
        "max_tokens": 10
    }
    
    print(f"Testing key: {key[:8]}...{key[-8:]}")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        if response.status_code == 200:
            result = response.json()
            print(f"DEBUG: Raw response: {json.dumps(result)}")
            if "choices" in result and result["choices"]:
                content = result["choices"][0].get("message", {}).get("content", "")
                if not content:
                    content = result["choices"][0].get("text", "")
                print(f"RESULT: {content.strip()}")
                return True
            else:
                print(f"RESULT: Received 200 but no choices in response: {result}")
                return False
        else:
            print(f"RESULT: Error {response.status_code}: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"RESULT: Connection error: {e}")
        return False

if __name__ == "__main__":
    if not api_keys:
        print("No API keys found in .env")
    else:
        for idx, key in enumerate(api_keys):
            print(f"\n--- Testing Key {idx+1} ---")
            test_key(key)
