from __future__ import annotations

import argparse
import glob
import json
import os
import re
import time
from typing import Any

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None  # type: ignore


def load_json(path: str) -> list[dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def key_by_name(item: dict[str, Any]) -> str:
    name = item.get("name")
    if not isinstance(name, str):
        return ""
    return re.sub(r"\s+", " ", name.strip()).casefold()


def dedupe_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for it in items:
        k = key_by_name(it)
        if not k:
            out.append(it)
            continue
        if k in seen:
            continue
        seen.add(k)
        out.append(it)
    return out


SYS_PROMPT = (
    "You are a precise Slovak→English translator. "
    "Translate the provided fields to English. Keep HTML tags and structure intact "
    "in the description (translate only text nodes). Preserve numbers, units, and prices. "
    "Output STRICT JSON with keys: name, description, category. If a source field is null, return null."
)


def extract_json(s: str) -> str:
    # Handle cases where the model wraps JSON in code fences
    m = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", s)
    return m.group(1) if m else s


def translate_record(client: Any, model: str, rec: dict[str, Any]) -> dict[str, Any]:
    name = rec.get("name")
    desc = rec.get("description")
    cat = rec.get("category")

    payload = {
        "name": name if isinstance(name, str) else None,
        "description": desc if isinstance(desc, str) else None,
        "category": cat if isinstance(cat, str) else None,
    }

    msg_user = (
        "Translate this JSON from Slovak to English. Keep HTML tags in description:\n"
        + json.dumps(payload, ensure_ascii=False)
    )
    resp = client.chat.completions.create(
        model=model,
        temperature=0.0,
        messages=[
            {"role": "system", "content": SYS_PROMPT},
            {"role": "user", "content": msg_user},
        ],
    )
    content = resp.choices[0].message.content or "{}"
    content = extract_json(content)
    out = json.loads(content)
    # Merge back into record
    rec = rec.copy()
    if out.get("name") is not None:
        rec["name"] = out["name"]
    if out.get("description") is not None:
        rec["description"] = out["description"]
    if out.get("category") is not None:
        rec["category"] = out["category"]
    return rec


def process_file(
    client: Any,
    model: str,
    in_path: str,
    out_path: str,
    sleep: float,
    dry_run: bool,
) -> None:
    items = load_json(in_path)
    items = dedupe_items(items)
    translated: list[dict[str, Any]] = []
    for it in items:
        if dry_run:
            translated.append(it)
            continue
        translated.append(translate_record(client, model, it))
        if sleep > 0:
            time.sleep(sleep)
    save_json(out_path, translated)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="De-duplicate by name and translate fields to English")
    p.add_argument("--in", dest="indir", default="data", help="Input directory with JSON files")
    p.add_argument("--out", dest="outdir", default="data_en", help="Output directory")
    p.add_argument("--pattern", default="*.json", help="Glob pattern for input files")
    p.add_argument("--model", default="gpt-4o-mini", help="OpenAI model name")
    p.add_argument("--sleep", type=float, default=0.0, help="Sleep between API calls (seconds)")
    p.add_argument(
        "--dry-run", action="store_true", help="Skip translation calls; just de-duplicate and copy"
    )
    args = p.parse_args(argv)

    os.makedirs(args.outdir, exist_ok=True)

    # Load .env from current directory if available
    if load_dotenv is not None:
        load_dotenv()

    client = None
    if not args.dry_run:
        if OpenAI is None:
            raise RuntimeError(
                "openai package not installed; run 'uv add openai' and create a .env with OPENAI_API_KEY=..."
            )
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError(
                "OPENAI_API_KEY missing. Create a .env file with OPENAI_API_KEY=... or set the environment variable."
            )
        client = OpenAI()

    in_glob = os.path.join(args.indir, args.pattern)
    files = sorted(glob.glob(in_glob))
    for fp in files:
        base = os.path.basename(fp)
        outp = os.path.join(args.outdir, base)
        process_file(client, args.model, fp, outp, args.sleep, args.dry_run)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
