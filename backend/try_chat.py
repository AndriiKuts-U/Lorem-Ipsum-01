import sys
import requests

BASE_URL = "http://localhost:8000"


def run(lat: float, lng: float) -> None:
    # 1) Fetch nearby places and append to first user message
    places_req = {"lat": lat, "lng": lng, "radius_m": 2000}
    pr = requests.post(f"{BASE_URL}/places/nearby", json=places_req)
    print("/places/nearby status:", pr.status_code)
    nearby_text = ""
    try:
        pdata = pr.json()
        items = pdata.get("places", [])[:10]
        if items:
            summary = ", ".join(f"{p['name']} ({p['distance_m']} m)" for p in items)
            nearby_text = f"\n\nNearby stores: {summary}."
    except Exception:
        pass

    # 2) Start chat with enriched user message
    chat_req = {"query": "hi" + nearby_text}
    r = requests.post(f"{BASE_URL}/chat", json=chat_req)
    print("/chat status:", r.status_code)
    data = r.json()
    thread_id = data.get("thread_id")
    print("thread_id:", thread_id)
    if not thread_id:
        print("No thread_id returned; aborting.")
        return

    # 3) Fetch thread messages and show the first user message
    rt = requests.get(f"{BASE_URL}/threads/{thread_id}")
    print("/threads/{id} status:", rt.status_code)
    t = rt.json()
    messages = t.get("messages", [])
    if messages:
        first_user = next((m for m in messages if m.get("role") == "user"), None)
        if first_user:
            print("First user message:")
            print(first_user.get("content"))
    else:
        print("No messages found.")


if __name__ == "__main__":
    # Default: Košice coords; allow overrides via CLI: python backend/try_chat.py 48.7318664 21.2431019
    lat = 48.7318664
    lng = 21.2431019
    if len(sys.argv) >= 3:
        lat = float(sys.argv[1])
        lng = float(sys.argv[2])
    run(lat, lng)
