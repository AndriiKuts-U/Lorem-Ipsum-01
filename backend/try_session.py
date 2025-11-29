import json
import uuid

import requests

BASE_URL = "http://localhost:8000"


def run(lat: float, lng: float, radius_m: int = 2000):
    thread_id = str(uuid.uuid4())
    print("thread_id:", thread_id)

    # 1) Set location for this thread
    set_payload = {"thread_id": thread_id, "lat": lat, "lng": lng, "radius_m": radius_m}
    r = requests.post(f"{BASE_URL}/session/location", json=set_payload)
    print("/session/location status:", r.status_code)
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))

    # 2) Chat using the same thread (agent should use stored deps)
    chat_payload = {
        "query": "What supermarkets are nearby?",
        "thread_id": thread_id,
        "use_retrieval": False,
    }
    rc = requests.post(f"{BASE_URL}/chat", json=chat_payload)
    print("/chat status:", rc.status_code)
    if rc.status_code != 200:
        print("chat error body:\n", rc.text)
        return
    chat = rc.json()
    print("assistant response:\n", chat.get("response"))

    # 3) Inspect thread messages (optional)
    rt = requests.get(f"{BASE_URL}/threads/{thread_id}")
    print("/threads/{id} status:", rt.status_code)
    data = rt.json()
    print("message_count:", data.get("message_count"))
    if isinstance(data.get("messages"), list) and data["messages"]:
        print("last message:", data["messages"][-1].get("content", ""))


if __name__ == "__main__":
    # Košice coords by default
    run(48.7318664, 21.2431019, 2000)
