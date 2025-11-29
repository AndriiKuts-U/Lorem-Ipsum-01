import os

import pytest
from fastapi.testclient import TestClient


def test_nearby_places_live(client: TestClient):
    if not os.getenv("GOOGLE_API_KEY"):
        pytest.skip("GOOGLE_API_KEY not set; skipping live Places test")

    payload = {"lat": 48.7318664, "lng": 21.2431019, "radius_m": 2000}
    r = client.post("/places/nearby", json=payload)

    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    assert "places" in data
    assert isinstance(data["places"], list)

    # If results exist, validate shape of first item
    if data["places"]:
        p = data["places"][0]
        assert isinstance(p.get("name"), str)
        assert isinstance(p.get("lat"), (int, float))
        assert isinstance(p.get("lng"), (int, float))
        assert isinstance(p.get("distance_m"), int)
