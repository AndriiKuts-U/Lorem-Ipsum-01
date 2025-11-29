import json
import os
from collections.abc import Iterable
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

BASE_URL = "https://places.googleapis.com/v1/places:searchNearby"


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    from math import asin, cos, radians, sin, sqrt

    R = 6371000.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return R * c


def _brand_key(n: str) -> str:
    import re
    import unicodedata

    nfkd = unicodedata.normalize("NFKD", n)
    ascii_only = nfkd.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", ascii_only).lower()
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned.split(" ")[0] if cleaned else n.strip().lower()


def find_nearby_places(
    lat: float,
    lng: float,
    *,
    radius_m: int = 5000,
    place_types: Iterable[str] | None = ("supermarket"),  # , "grocery_store"
    min_unique: int = 20,
    max_pages: int = 5,
    max_per_brand: int = 1,
) -> list[dict[str, Any]]:
    if not GOOGLE_API_KEY:
        raise RuntimeError("GOOGLE_API_KEY is not set")

    types = list(place_types) if place_types else ["supermarket"]
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_API_KEY,
        "X-Goog-FieldMask": "places.id,places.displayName,places.location",
    }

    payload = {
        "includedTypes": types,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": radius_m,
            }
        },
        "rankPreference": "DISTANCE",
        "maxResultCount": 20,
    }

    seen_place_ids: set[str] = set()
    results: list[tuple[float, str, float, float, str]] = []

    page_token: str | None = None
    pages = 0
    while pages < max_pages and len(results) < min_unique:
        body = dict(payload)
        if page_token:
            body["pageToken"] = page_token

        resp = requests.post(BASE_URL, headers=headers, data=json.dumps(body))
        resp.raise_for_status()
        data = resp.json()

        for place in data.get("places", []):
            pid = place.get("id")
            if not pid or pid in seen_place_ids:
                continue
            seen_place_ids.add(pid)
            name = place.get("displayName", {}).get("text", "N/A")
            loc = place.get("location") or {}
            plat = loc.get("latitude")
            plng = loc.get("longitude")
            if plat is None or plng is None:
                continue
            dist_m = _haversine_m(lat, lng, plat, plng)
            results.append((dist_m, name, plat, plng, pid))

        page_token = data.get("nextPageToken")
        pages += 1
        if not page_token:
            break

    results.sort(key=lambda x: x[0])

    # Optional brand cap to keep variety
    if max_per_brand > 0:
        brand_counts: dict[str, int] = {}
        filtered: list[tuple[float, str, float, float, str]] = []
        for item in results:
            _, name, *_ = item
            bk = _brand_key(name)
            cnt = brand_counts.get(bk, 0)
            if cnt >= max_per_brand:
                continue
            brand_counts[bk] = cnt + 1
            filtered.append(item)
        results = filtered

    return [
        {
            "distance_m": int(dist),
            "name": name,
            "lat": plat,
            "lng": plng,
            "place_id": pid,
        }
        for dist, name, plat, plng, pid in results
    ]


if __name__ == "__main__":
    # Simple CLI test: geocode an address and print nearby places
    import sys

    test_address = "Nemcová 5, Košice, Slovakia"
    if len(sys.argv) > 1:
        test_address = " ".join(sys.argv[1:])

    g_url = "https://maps.googleapis.com/maps/api/geocode/json"
    g_params = {"address": test_address, "key": GOOGLE_API_KEY}
    r = requests.get(g_url, params=g_params)
    j = r.json()
    if j.get("status") != "OK":
        print("Geocode error:", j.get("status"), j.get("error_message"))
        raise SystemExit(1)
    loc = j["results"][0]["geometry"]["location"]
    print(f"Coordinates for '{test_address}': {loc['lat']}, {loc['lng']}")
    places = find_nearby_places(loc["lat"], loc["lng"])
    for i, p in enumerate(places, start=1):
        print(f"{i}. {p['distance_m']} m - {p['name']} ({p['lat']}, {p['lng']})")
