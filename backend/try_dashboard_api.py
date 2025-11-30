import json

import requests

BASE_URL = "http://127.0.0.1:8000"


def run() -> None:
    r = requests.get(f"{BASE_URL}/dashboard")
    print("GET /dashboard status:", r.status_code)
    try:
        data = r.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception:
        print("Raw response:", r.text)


if __name__ == "__main__":
    run()
