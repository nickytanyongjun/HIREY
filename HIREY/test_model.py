import requests
import json

API_KEY = "YOUR_CHUTES_API_KEY"

MODEL_NAME = "YOUR_MODEL"

url = "https://llm.chutes.ai/v1/chat/completions"

headers = {

    "Authorization":
        f"Bearer {API_KEY}",

    "Content-Type":
        "application/json"
}

payload = {

    "model": MODEL_NAME,

    "messages": [

        {
            "role": "user",
            "content": "Hello"
        }

    ],

    "max_tokens": 50
}

response = requests.post(

    url,

    headers=headers,

    json=payload
)

print("STATUS:")
print(response.status_code)

print("\nRESPONSE:\n")

print(response.text)