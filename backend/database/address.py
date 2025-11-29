import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

address = "Nemcová 5, Košice, Slovakia"

url = "https://maps.googleapis.com/maps/api/geocode/json"
params = {"address": address, "key": GOOGLE_API_KEY}

response = requests.get(url, params=params)
data = response.json()

if data["status"] == "OK":
    location = data["results"][0]["geometry"]["location"]
    lat = location["lat"]
    lng = location["lng"]
    print(f"Coordinates for '{address}': {lat}, {lng}")
else:
    print("Error:", data.get("status"), data.get("error_message"))
    exit()

LOCATION_LAT = lat
LOCATION_LNG = lng

# Radius in meters (e.g., 1500m or 1.5 km)
RADIUS_METERS = 1500

# Type of place to search for (e.g., 'supermarket')
# The new API uses Place Types defined in their documentation.
PLACE_TYPE = "supermarket"

# Base URL for the new Nearby Search endpoint
BASE_URL = "https://places.googleapis.com/v1/places:searchNearby"

# Define the data payload for the POST request
payload = {
    "includedTypes": [PLACE_TYPE],
    "locationRestriction": {
        "circle": {
            "center": {"latitude": LOCATION_LAT, "longitude": LOCATION_LNG},
            "radius": RADIUS_METERS,
        }
    },
    # Set maximum results to return (up to 20)
    "maxResultCount": 10,
}

# The new API requires specifying the fields you want to retrieve
# This saves bandwidth and reduces billing.
headers = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": GOOGLE_API_KEY,
    # Define the fields you want in the response (essential for New API)
    "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating",
}

# --- 4. Make the POST Request ---
print(f"Searching for {PLACE_TYPE} within {RADIUS_METERS}m using Places API (New)...")
try:
    response = requests.post(BASE_URL, headers=headers, data=json.dumps(payload))
    response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

    # --- 5. Process the JSON Response ---
    data = response.json()

    if data.get("places"):
        print(f"\n✅ Found {len(data['places'])} markets:")
        for i, place in enumerate(data["places"]):
            name = place.get("displayName", {}).get("text", "N/A")
            address = place.get("formattedAddress", "N/A")
            rating = place.get("rating", "N/A")

            print(f"  {i + 1}. {name}")
            print(f"     Address: {address}")
            print(f"     Rating: {rating}")
            print("-" * 20)
    else:
        print("\n⚠️ No results found or 'places' field is empty.")
        # Check for potential API errors returned in the response body
        if response.status_code != 200:
            print(
                f"   API returned Status Code {response.status_code}: {data.get('error', {}).get('message', 'No specific error message.')}"
            )

except requests.exceptions.RequestException as e:
    print(f"\nAn error occurred during the request: {e}")
