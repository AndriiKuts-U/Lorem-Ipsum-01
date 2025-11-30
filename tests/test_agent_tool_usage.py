import os
from typing import Any
from pathlib import Path
import pytest
from anyio import fail_after
from dotenv import load_dotenv
import uuid

from backend.agent_ai import ChatDeps, agent

pytestmark = pytest.mark.integration
load_dotenv()


def _env_ok() -> bool:
    return bool(os.getenv("OPENAI_API_KEY")) and bool(os.getenv("GOOGLE_API_KEY"))


@pytest.mark.anyio
@pytest.mark.skipif(not _env_ok(), reason="Requires OPENAI_API_KEY and GOOGLE_API_KEY")
async def test_agent_calls_find_nearby_tool_and_returns_summary(tmp_path: Path) -> None:
    thread_id = str(uuid.uuid4())
    deps = ChatDeps(
        lat=48.7318664,
        lng=21.2431019,
        radius_m=1500,
        types=["supermarket"],
        max_per_brand=1,
        thread_id=thread_id,
    )

    prompt = "Use your nearby places tool to find supermarkets around me and list the top 5 with distances."

    deps_cast: Any = deps
    with fail_after(30):
        result = await agent.run(prompt, deps=deps_cast)

    # Inspect messages to confirm a tool call occurred
    msgs = result.all_messages()
    serialized = "\n".join(str(m) for m in msgs)
    assert (
        "tool_name='find_nearby_places'" in serialized
        or 'tool_name="find_nearby_places"' in serialized
    )
    assert "ToolReturnPart" in serialized

    # The output should mention some stores or distances
    out = str(result.output)
    assert any(
        k in out.lower() for k in ["lidl", "billa", "fresh", "kaufland", "meters", "m "]
    )  # heuristic


@pytest.mark.anyio
@pytest.mark.skipif(not _env_ok(), reason="Requires OPENAI_API_KEY and GOOGLE_API_KEY")
async def test_tool_persists_full_places_to_thread_data(tmp_path: Path) -> None:
    thread_id = str(uuid.uuid4())
    deps = ChatDeps(
        lat=48.7318664,
        lng=21.2431019,
        radius_m=1200,
        types=["supermarket", "grocery_store"],
        max_per_brand=1,
        thread_id=thread_id,
    )

    deps_cast: Any = deps
    with fail_after(30):
        await agent.run("Please use your nearby tool and summarize results.", deps=deps_cast)

    td_path = os.path.join("backend", "thread_data", f"{thread_id}.json")
    assert os.path.exists(td_path), f"thread_data file not found: {td_path}"

    import json

    with open(td_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    assert "places" in data, "places not persisted in thread_data"
    assert isinstance(data["places"], list) and len(data["places"]) > 0
    sample = data["places"][0]
    # persisted places should include coordinates for frontend usage
    assert "lat" in sample and "lng" in sample
