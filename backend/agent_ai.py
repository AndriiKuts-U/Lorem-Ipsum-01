from dataclasses import dataclass
from typing import Any

from pydantic_ai import Agent, RunContext

from backend.maps.address import find_nearby_places as _find_nearby_places

SYSTEM_PROMPT = (
    "You are a helpful shopping assistant."
    " Answer concisely and prefer concrete, actionable suggestions."
    " When the user asks about nearby markets or stores,"
    " use the find_nearby_places tool based on the stored location context,"
    " then summarize the top nearby options."
)


@dataclass
class ChatDeps:
    lat: float
    lng: float
    radius_m: int
    types: list[str]
    max_per_brand: int = 1


# Single shared agent instance using OpenAI via Pydantic AI
agent: Agent = Agent(
    model="openai:gpt-4o-mini",
    system_prompt=SYSTEM_PROMPT,
    deps_type=ChatDeps,
)


@agent.tool
def find_nearby_places(ctx: RunContext[ChatDeps | None], top_k: int = 5) -> list[dict[str, Any]]:
    """Find nearby markets from stored location context and return only name + distance.

    top_k: number of places to return
    """
    if ctx.deps is None:
        raise RuntimeError("Location context is not set for this conversation.")
    deps = ctx.deps
    places = _find_nearby_places(
        deps.lat,
        deps.lng,
        radius_m=deps.radius_m,
        place_types=deps.types,
        min_unique=20,
        max_pages=5,
        max_per_brand=deps.max_per_brand,
    )
    return [{"name": p["name"], "distance_m": p["distance_m"]} for p in places[: max(1, top_k)]]
