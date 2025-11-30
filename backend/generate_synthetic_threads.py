import json
import uuid
from collections.abc import Iterable
from pathlib import Path

THREAD_DIR = Path("./backend/thread_memory")
THREAD_DIR.mkdir(parents=True, exist_ok=True)


def make_thread(thread_id: str, messages: Iterable[dict]) -> None:
    f = THREAD_DIR / f"{thread_id}.json"
    with f.open("w", encoding="utf-8") as fh:
        json.dump(list(messages), fh, ensure_ascii=False, indent=2)


def main():
    threads: dict[str, list[dict]] = {}

    # Thread A: includes nearby summary first, then shopping list, then recipe
    t1 = str(uuid.uuid4())
    threads[t1] = [
        {
            "role": "user",
            "content": "hi\n\nNearby stores: Lidl (520 m), BILLA (1200 m), Kaufland (1500 m).",
        },
        {"role": "user", "content": "Shopping list: tomatoes, lettuce, chicken breast, apples"},
        {"role": "assistant", "content": "Recipe: chicken salad"},
        {"role": "user", "content": "Shopping list: olive oil, lemon"},
    ]

    # Thread B: mixed diet with recipe and a 3-6 ingredients list
    t2 = str(uuid.uuid4())
    threads[t2] = [
        {
            "role": "user",
            "content": "Hello\n\nNearby stores: Tesco (800 m), FRESH Plus (950 m), KLAS (1300 m).",
        },
        {"role": "user", "content": "Shopping list: milk, bread, chocolate, bananas"},
        {"role": "assistant", "content": "Recipe: french toast"},
        {"role": "user", "content": "Shopping list: pizza, broccoli, yogurt"},
    ]

    # Thread C: high-calorie leaning with explicit recipe
    t3 = str(uuid.uuid4())
    threads[t3] = [
        {
            "role": "user",
            "content": "hi\n\nNearby stores: FRESH Plus Merkúr (100 m), BILLA (1017 m).",
        },
        {"role": "user", "content": "Shopping list: bacon, butter, cake, fries, soda"},
        {"role": "assistant", "content": "Recipe: loaded fries"},
        {"role": "user", "content": "Shopping list: cheddar, sour cream"},
    ]

    created = []
    for tid, msgs in threads.items():
        make_thread(tid, msgs)
        created.append(tid)
        print("Created thread:", tid)

    # Only compute analytics for these 3 threads
    try:
        from backend.analytics import StatsService

        svc = StatsService()
        for tid in created:
            svc.compute_and_store(tid, recompute=False)
    except Exception:
        pass


if __name__ == "__main__":
    main()
