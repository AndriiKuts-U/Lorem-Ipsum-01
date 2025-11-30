import sys
import uuid

import requests

BASE_URL = "http://127.0.0.1:8000"


def run(lat: float, lng: float) -> None:
    thread_id = str(uuid.uuid4())
    # 1) Set session location first
    loc_req = {"thread_id": thread_id, "lat": lat, "lng": lng}
    rs = requests.post(
        f"{BASE_URL}/session/location",
        json=loc_req,
        timeout=10,
    )
    print("/session/location status:", rs.status_code)
    if rs.status_code != 200:
        try:
            print("location error:", rs.text)
        except Exception:
            pass
        return

    # 2) Start chat on the same thread
    chat_req = {"query": "hi", "thread_id": thread_id}
    r = requests.post(f"{BASE_URL}/chat", json=chat_req)
    print("/chat status:", r.status_code)
    if r.status_code != 200:
        try:
            print("chat error:", r.text)
        except Exception:
            pass
        return

    data = r.json()
    print("thread_id:", data.get("thread_id"))
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
