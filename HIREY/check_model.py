import requests
import json

API_KEY = "YOUR_CHUTES_API_KEY"

# ==========================================
# GET MODELS
# ==========================================

url = "https://llm.chutes.ai/v1/models"

headers = {
    "Authorization": f"Bearer {API_KEY}"
}

response = requests.get(
    url,
    headers=headers
)

print("STATUS:", response.status_code)

data = response.json()

print("\n====================")
print("AVAILABLE MODELS")
print("====================\n")

# ==========================================
# PRINT MODELS
# ==========================================

if "data" in data:

    for model in data["data"]:

        model_id = model.get("id")

        print(model_id)

else:

    print(json.dumps(data, indent=4))