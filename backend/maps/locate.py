# import os

# import requests
# from dotenv import load_dotenv

# load_dotenv()

# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# url = f"https://www.googleapis.com/geolocation/v1/geolocate?key={GOOGLE_API_KEY}"

# response = requests.post(url)
# data = response.json()

# if "location" in data:
#     lat = data["location"]["lat"]
#     lng = data["location"]["lng"]
#     accuracy = data.get("accuracy", "N/A")
#     print(f"Location: {lat}, {lng} (±{accuracy} meters)")
# elif "error" in data:
#     print("Error from API:", data["error"]["message"])
# else:
#     print("Unexpected response:", data)
