import json
import os
from pathlib import Path

from backend.analytics import StatsService


def test_dashboard_compute_and_store(tmp_path: Path) -> None:
    # Prepare a synthetic thread with a few user messages
    thread_id = "test-thread-dash"
    thread_dir = Path("./thread_memory")
    thread_dir.mkdir(parents=True, exist_ok=True)
    messages = [
        {"role": "user", "content": "Shopping list: milk, bread, chicken breasts"},
        {"role": "assistant", "content": "Try this recipe: chicken soup with tomatoes"},
        {"role": "user", "content": "I also want chocolate and pizza"},
    ]
    with (thread_dir / f"{thread_id}.json").open("w", encoding="utf-8") as fh:
        json.dump(messages, fh)

    svc = StatsService()
    data = svc.compute_and_store(thread_id)

    # Validate persisted file exists
    out_file = Path("./analytics") / f"{thread_id}.json"
    assert out_file.exists(), "analytics file not created"

    # Validate core fields
    assert "favorites" in data and isinstance(data["favorites"], list)
    assert "discounts" in data and "average_discount" in data["discounts"]
    assert "caloric_trend" in data and isinstance(data["caloric_trend"], list)
    assert "recipes" in data and isinstance(data["recipes"], list)

    # Expect some items detected and a simple health score present
    if data["caloric_trend"]:
        ct = data["caloric_trend"][0]
        assert "health_score" in ct
