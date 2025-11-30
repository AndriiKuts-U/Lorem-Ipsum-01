import json
from pathlib import Path

from backend.analytics import StatsService, ANALYTICS_DIR


def run() -> None:
    svc = StatsService()
    data = svc.compute_all(recompute=False)
    print("Aggregate dashboard computed. Summary keys:", list(data.keys()))

    # List per-thread analytics files
    print("Analytics directory:", ANALYTICS_DIR)
    if ANALYTICS_DIR.exists():
        files = list(ANALYTICS_DIR.glob("*.json"))
        print(f"Found {len(files)} analytics files:")
        for p in files[:20]:
            print(" -", p)
            try:
                with p.open("r", encoding="utf-8") as fh:
                    js = json.load(fh)
                print("   favorites:", [f.get("name") for f in js.get("favorites", [])[:5]])
            except Exception:
                pass
    else:
        print("Analytics directory does not exist.")


if __name__ == "__main__":
    run()
