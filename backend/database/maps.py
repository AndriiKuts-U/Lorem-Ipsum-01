import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

url = "https://places.googleapis.com/v1/places:searchText"

headers = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": GOOGLE_API_KEY,
    "X-Goog-FieldMask": "places.displayName,places.formattedAddress",
}

payload = {"textQuery": "pizza in Berlin"}

response = requests.post(url, headers=headers, json=payload)

print("Status:", response.status_code)
print("Response:")
print(json.dumps(response.json(), indent=2))
