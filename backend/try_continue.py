import uuid

import requests

BASE_URL = "http://127.0.0.1:8000"


def run(lat: float, lng: float, radius_m: int = 2000):
    thread_id = str(uuid.uuid4())
    print("thread_id:", thread_id)

    # 1) Set location once for this thread
    r = requests.post(
        f"{BASE_URL}/session/location",
        json={"thread_id": thread_id, "lat": lat, "lng": lng, "radius_m": radius_m},
    )
    print("/session/location:", r.status_code)

    def chat(q: str):
        rc = requests.post(f"{BASE_URL}/chat", json={"query": q, "thread_id": thread_id})
        print("/chat:", rc.status_code)
        if rc.status_code != 200:
            print("error:", rc.text)
            return None
        data = rc.json()
        print("assistant:\n", data.get("response"))
        return data

    # 2) First turn: asks for nearby
    chat("What supermarkets are nearby?")

    # 3) Second turn: continuity check
    chat("Based on those, suggest a quick breakfast shopping list under €10.")

    # 4) Third turn: memory recall
    chat("Remind me which stores you mentioned first.")

    # 5) Inspect thread state
    rt = requests.get(f"{BASE_URL}/threads/{thread_id}")
    print("/threads:", rt.status_code)
    if rt.status_code == 200:
        t = rt.json()
        print("message_count:", t.get("message_count"))
        msgs = t.get("messages", [])
        print("last message preview:", (msgs[-1].get("content") if msgs else "")[:200])


if __name__ == "__main__":
    run(48.7318664, 21.2431019, 2000)
