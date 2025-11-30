import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.agent_ai import agent
from backend.settings import settings
from openai import OpenAI


ANALYTICS_DIR = Path("./backend/thread_analytics")
ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)


class StatsService:
    def __init__(self) -> None:
        self.thread_dir = Path("./backend/thread_memory")
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def list_thread_ids(self) -> list[str]:
        if not self.thread_dir.exists():
            return []
        return [p.stem for p in self.thread_dir.glob("*.json")]

    def _load_thread_messages(self, thread_id: str) -> list[dict]:
        f = self.thread_dir / f"{thread_id}.json"
        if not f.exists():
            return []
        with f.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def _extract_recipe_titles(self, messages: list[dict]) -> list[dict[str, Any]]:
        titles: list[dict[str, Any]] = []
        for m in messages:
            content = str(m.get("content", ""))
            low = content.lower()
            if "ingredients" in low:
                continue
            if "recipe:" in low:
                # Grab text after 'recipe:' up to newline or punctuation
                after = content.split(":", 1)[1].strip() if ":" in content else content
                name = after.split("\n", 1)[0].strip()
                # Keep a short title (words only)
                name = " ".join(w for w in name.split() if w.isalpha() or w.isalnum())
                if name:
                    titles.append({"title": name[:80]})
        return titles

    def _analyze_messages(self, messages: list[dict]) -> dict[str, Any]:
        # Extract items from user messages using the agent tool
        item_counter: Counter[str] = Counter()
        items_to_products: dict[str, list[dict]] = defaultdict(list)
        recipes: list[dict[str, Any]] = self._extract_recipe_titles(messages)

        for m in messages:
            if m.get("role") != "user":
                continue
            content = str(m.get("content", "")).strip()
            if not content:
                continue
            # Hint the agent to use the extraction tool
            prompt = f"Shopping list: {content}"
            try:
                result = agent.run_sync(prompt)
                # Heuristic: the tool logs are visible in messages; but we need structured items.
                # For simplicity parse back from messages if tool returned items.
                # Otherwise, fall back to naive token split.
                # We keep this minimal and robust.
                output_text = str(result.output)
                # Naive split by commas as fallback
                candidates = [t.strip().lower() for t in output_text.split(",") if t.strip()]
                for name in candidates:
                    if len(name) > 2 and all(c.isalnum() or c.isspace() for c in name):
                        item_counter[name] += 1
            except Exception:
                # Fallback: naive extraction from content
                tokens = [t.strip().lower() for t in content.split(",") if t.strip()]
                for name in tokens:
                    if len(name) > 2 and all(c.isalnum() or c.isspace() for c in name):
                        item_counter[name] += 1

        favorites = [{"name": name, "count": cnt} for name, cnt in item_counter.most_common(20)]

        # Optimistic discount metrics (if later we attach product payloads)
        discounts: list[float] = []
        discounted_items = 0
        for name, _ in item_counter.items():
            products = items_to_products.get(name, [])
            best = 0.0
            for p in products:
                try:
                    best = max(best, float(p.get("discount", 0.0)))
                except Exception:
                    pass
            if best > 0:
                discounted_items += 1
            discounts.append(best)

        avg_discount = sum(discounts) / len(discounts) if discounts else 0.0
        capture_rate = (discounted_items / len(item_counter)) if item_counter else 0.0

        # Very simple health scoring heuristic from extracted items
        high_cal = {"chocolate", "bacon", "butter", "cake", "pizza", "fries", "soda"}
        healthy = {"tomato", "salad", "lettuce", "chicken breast", "fish", "broccoli", "apple"}
        high_hits = sum(
            cnt for name, cnt in item_counter.items() if any(h in name for h in high_cal)
        )
        healthy_hits = sum(
            cnt for name, cnt in item_counter.items() if any(h in name for h in healthy)
        )
        score = 3
        if healthy_hits > high_hits * 2:
            score = 5
        elif healthy_hits > high_hits:
            score = 4
        elif high_hits > healthy_hits * 2:
            score = 2
        elif high_hits > healthy_hits:
            score = 3

        stats = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "favorites": favorites,
            "caloric_trend": [
                {
                    "high_calorie_mentions": int(high_hits),
                    "healthy_mentions": int(healthy_hits),
                    "health_score": score,  # 1-5
                }
            ],
            "recommendations": [],  # extend later
            "recipes": recipes,
            "discounts": {
                "average_discount": round(avg_discount, 3),
                "capture_rate": round(capture_rate, 3),
            },
        }
        return stats

    def compute_and_store(self, thread_id: str, *, recompute: bool = False) -> dict[str, Any]:
        out_file = ANALYTICS_DIR / f"{thread_id}.json"
        if out_file.exists() and not recompute:
            with out_file.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        messages = self._load_thread_messages(thread_id)
        stats = self._analyze_messages(messages)
        with out_file.open("w", encoding="utf-8") as fh:
            json.dump(stats, fh, ensure_ascii=False, indent=2)
        return stats

    def load(self, thread_id: str) -> dict[str, Any] | None:
        f = ANALYTICS_DIR / f"{thread_id}.json"
        if not f.exists():
            return None
        with f.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def _health_summary(self, favorites: list[dict], recipes: list[dict]) -> str:
        # Build a compact prompt for a quick summary
        fav_str = ", ".join(f.get("name", "") for f in favorites[:10] if f.get("name"))
        rec_str = ", ".join(r.get("title", "") for r in recipes[:10] if r.get("title"))
        sys = (
            "You are a nutrition assistant. Given favorite foods and recipe titles from a user's chat, "
            "provide a brief two-sentence health trend summary and one suggestion to improve diet."
        )
        user = f"Favorites: {fav_str}\nRecipes: {rec_str}\nSummarize health trend and give a quick suggestion."
        try:
            res = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": sys}, {"role": "user", "content": user}],
            )
            return res.choices[0].message.content or ""
        except Exception:
            return "Health trend summary unavailable at the moment."

    def compute_all(self, recompute: bool = False) -> dict[str, Any]:
        threads: dict[str, Any] = {}
        all_favorites: Counter[str] = Counter()
        all_recipes: list[dict] = []

        for tid in self.list_thread_ids():
            stats = None
            if not recompute:
                stats = self.load(tid)
            if stats is None:
                stats = self.compute_and_store(tid, recompute=False)
            threads[tid] = stats
            for fav in stats.get("favorites", []):
                name = str(fav.get("name", "")).strip().lower()
                count = int(fav.get("count", 0))
                if name:
                    all_favorites[name] += count
            all_recipes.extend(stats.get("recipes", []))

        fav_agg = [{"name": n, "count": c} for n, c in all_favorites.most_common(20)]
        health = self._health_summary(fav_agg, all_recipes)
        return {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "threads": threads,
            "health_summary": health,
            "favorites_aggregate": fav_agg,
        }
