import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openai import OpenAI
from pydantic import BaseModel

from backend.settings import settings

ANALYTICS_DIR = Path("./thread_analytics")
ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)


class StatsService:
    def __init__(self) -> None:
        self.thread_dir = Path("./thread_memory")
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
        # Use LLM structured output to extract top-3 favorites and recipe titles
        class ThreadExtract(BaseModel):
            favorites: list[str] = []
            recipes: list[str] = []
            recommendations: str = ""

        conv_lines: list[str] = []
        for m in messages:
            role = str(m.get("role", ""))
            content = str(m.get("content", "")).strip()
            if content:
                conv_lines.append(f"{role}: {content}")
        convo = "\n".join(conv_lines)

        sys = (
            "Extract top-3 favorite grocery items (names only) and top-3 recipe/meal titles (short), "
            "plus up to 3 short personalized suggestions. Return lists only."
        )
        try:
            comp = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": sys}, {"role": "user", "content": convo}],
                response_format=ThreadExtract,
            )
            parsed: ThreadExtract = comp.choices[0].message.parsed  # type: ignore
            favs = [{"name": n, "count": 1} for n in parsed.favorites[:3]]
            recs = [{"title": t} for t in parsed.recipes[:3]]
            # single recommendation string (first suggestion if present)
            rec_str = parsed.recommendations[0] if parsed.recommendations else ""
            return {
                "favorites": favs,
                "recipes": recs,
                "recommendation": rec_str,
            }
        except Exception:
            # Fallback: use only recipe titles from messages and simple token split for favorites
            item_counter: Counter[str] = Counter()
            recipes = self._extract_recipe_titles(messages)
            for m in messages:
                if m.get("role") != "user":
                    continue
                content = str(m.get("content", ""))
                tokens = [t.strip().lower() for t in content.split(",") if t.strip()]
                for name in tokens:
                    if len(name) > 2 and all(c.isalnum() or c.isspace() for c in name):
                        item_counter[name] += 1
            favs = [{"name": n, "count": c} for n, c in item_counter.most_common(3)]
            return {"favorites": favs, "recipes": recipes, "recommendation": ""}

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

    def compute_all(self, recompute: bool = False) -> dict[str, Any]:
        all_favorites: Counter[str] = Counter()
        recipe_titles: Counter[str] = Counter()

        for tid in self.list_thread_ids():
            stats = None
            if not recompute:
                stats = self.load(tid)
            if stats is None:
                stats = self.compute_and_store(tid, recompute=False)
            for fav in stats.get("favorites", []):
                name = str(fav.get("name", "")).strip().lower()
                count = int(fav.get("count", 0))
                if name:
                    all_favorites[name] += count
            for rec in stats.get("recipes", []):
                title = str(rec.get("title", "")).strip().lower()
                if title:
                    recipe_titles[title] += 1

        top_fav = [{"name": n, "count": c} for n, c in all_favorites.most_common(3)]
        top_recipes = [{"title": t, "count": c} for t, c in recipe_titles.most_common(3)]
        return {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "top_favorites": top_fav,
            "top_recipes": top_recipes,
        }
