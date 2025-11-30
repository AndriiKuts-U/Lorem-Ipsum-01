import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openai import OpenAI
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIResponsesModelSettings
from qdrant_client import QdrantClient

from backend.settings import settings
from backend.maps.address import find_nearby_places as _find_nearby_places

model_settings = OpenAIResponsesModelSettings(
    openai_reasoning_effort="minimal",
    openai_reasoning_summary="concise",
)

# Initialize OpenAI client for structured outputs
openai_client = OpenAI()

# Initialize Qdrant client for product search
qdrant_client = QdrantClient(url=settings.QDRANT_DATABASE_URL, api_key=settings.QDRANT_API_KEY)


SYSTEM_PROMPT = (
    "You are a helpful shopping assistant that helps users find the best stores for their grocery shopping."
    " Answer concisely and prefer concrete, actionable suggestions."
    "\n\n1. When the user asks about nearby markets or stores,"
    " use the find_nearby_places tool based on the stored location context,"
    " then summarize the top nearby options."
    "\n\n2. When user asks about a specific product, return the product name and price."
    "\n\n3. When the user provides a shopping list, use the extract_shopping_list tool."
    " This tool will:"
    " - Extract all grocery items from their input"
    " - Search for similar products available in stores with prices"
    " - Return detailed product information including store names, prices, and availability"
    "\n\nThen analyze the results and:"
    " - Compare prices across different stores"
    " - Calculate total costs per store"
    " - Recommend the best store(s) to visit based on:"
    "   * Total cost (cheapest option)"
    "   * Product availability (stores that have most items)"
    "   * Value for money"
    " - Provide a clear breakdown showing:"
    "   * Which items are available at which stores"
    "   * Price per item at each store"
    "   * Total cost if shopping at each store"
    "   * Your final recommendation with reasoning"
)


class GroceryItem(BaseModel):
    """A single grocery item extracted from user input."""

    name: str
    quantity: str | None = None


class ShoppingList(BaseModel):
    """A structured shopping list extracted from user input."""

    items: list[GroceryItem]


@dataclass
class ChatDeps:
    lat: float
    lng: float
    radius_m: int
    types: list[str]
    max_per_brand: int = 1
    # thread id to persist tool results into thread-scoped data
    thread_id: str | None = None


# Single shared agent instance using OpenAI via Pydantic AI
agent: Agent = Agent(
    model="openai:gpt-5-mini",
    system_prompt=SYSTEM_PROMPT,
    deps_type=ChatDeps,
    model_settings=model_settings,
)

qdrant = QdrantClient(
    url=settings.QDRANT_DATABASE_URL,
    api_key=settings.QDRANT_API_KEY,
)


def _get_embedding(text: str) -> list[float]:
    """Get embedding vector for text using OpenAI embeddings."""
    response = openai_client.embeddings.create(model="text-embedding-3-small", input=text)
    return response.data[0].embedding


def retrieve_context(query: str, top_k: int = 3, include_metadata: bool = False) -> list[dict]:
    """Retrieve relevant documents from Qdrant."""

    query_embedding = _get_embedding(query)

    results = qdrant.query_points(
        collection_name="groceries",
        query=query_embedding,
        limit=top_k,
        with_payload=True,
    )
    # print(results)
    out = []
    for hit in results.points:
        payload = hit.payload or {}
        text_val = payload.get("text", "")

        result = {
            "text": text_val,
            "score": hit.score,
        }

        # Include full metadata if requested
        if include_metadata:
            result.update(payload)

        out.append(result)
    return out


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
    # Persist full places (with coords) into thread_data if we know the thread
    if deps.thread_id:
        td_dir = Path("./backend/thread_data")
        td_dir.mkdir(parents=True, exist_ok=True)
        td_file = td_dir / f"{deps.thread_id}.json"
        data: dict[str, Any] = {}
        if td_file.exists():
            try:
                with td_file.open("r", encoding="utf-8") as fh:
                    data = json.load(fh)
            except Exception:
                data = {}
        data["places"] = places  # full payload incl. lat/lng
        try:
            with td_file.open("w", encoding="utf-8") as fh:
                json.dump(data, fh)
        except Exception:
            # fail-soft on persistence
            pass

    # Return minimal info to the model (name + distance only)
    return [{"name": p["name"], "distance_m": p["distance_m"]} for p in places[: max(1, top_k)]]


@agent.tool
def extract_shopping_list(
    ctx: RunContext[ChatDeps | None],
    user_input: str,
    top_k_per_item: int = 10,
) -> dict[str, Any]:
    """Extract grocery items from user's shopping list and find similar products in stores.

    This tool:
    1. Parses natural language shopping lists using GPT structured output
    2. For each item, searches Qdrant for similar products available in stores
    3. Returns structured data with product prices, stores, and availability

    Args:
        user_input: The user's shopping list in natural language (e.g., "I need milk, bread, 2kg tomatoes, and chicken")
        top_k_per_item: Number of similar products to find per item (default: 10)

    Returns:
        A dictionary containing extracted items with their store availability and prices
    """
    try:
        # Log tool invocation
        # Note: we do not persist this result; it's ephemeral for analysis
        # Logging here helps tests observe tool usage
        import logging

        tool_log = logging.getLogger("agent.tools")

        tool_log.info(
            "extract_shopping_list called: thread_id=%s items_hint=%s top_k_per_item=%s",
            getattr(ctx.deps, "thread_id", None) if ctx.deps else None,
            user_input[:50].replace("\n", " "),
            top_k_per_item,
        )
        # Step 1: Extract grocery items using structured output
        completion = openai_client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert at parsing shopping lists. "
                        "Extract all grocery items from the user's input, including quantities if mentioned. "
                    ),
                },
                {"role": "user", "content": user_input},
            ],
            response_format=ShoppingList,
        )

        shopping_list = completion.choices[0].message.parsed
        # Log actual ingredient names parsed
        try:
            names_list = [getattr(i, "name", "") for i in shopping_list.items]  # type: ignore[attr-defined]
        except Exception:
            names_list = []
        tool_log.info("extract_shopping_list ingredients=%s", ", ".join(n for n in names_list if n))
        # Count parsed items and warn on unusually large lists
        try:
            parsed_count = len(shopping_list.items)  # type: ignore[attr-defined]
        except Exception:
            parsed_count = 0
        tool_log.info("extract_shopping_list parsed items_count=%s", parsed_count)
        if parsed_count > 50:
            tool_log.warning("extract_shopping_list large item count: %s > %s", parsed_count, 50)

        # Step 2: For each item, search Qdrant for similar products
        items_with_products = []
        for item in shopping_list.items:  # type: ignore[attr-defined]
            # Search for similar products in Qdrant
            tool_log.info(
                "extract_shopping_list searching item=%s top_k=%s",
                getattr(item, "name", ""),
                top_k_per_item,
            )
            similar_products = retrieve_context(
                query=item.name, top_k=top_k_per_item, include_metadata=True
            )
            tool_log.info(
                "extract_shopping_list found=%s for item=%s",
                len(similar_products),
                getattr(item, "name", ""),
            )

            items_with_products.append(
                {
                    "name": item.name,
                    "quantity": item.quantity,
                    "similar_products": similar_products,
                }
            )

        # Step 3: Compile the data for GPT to analyze
        result = {
            "items": items_with_products,
            "total_items": len(items_with_products),
            "user_input": user_input,
        }
        tool_log.info(
            "extract_shopping_list extracted %d items: %s",
            len(items_with_products),
            ", ".join(i.get("name", "") for i in items_with_products if i.get("name")),
        )
        return result

    except Exception as e:
        import logging

        logging.getLogger("agent.tools").warning("extract_shopping_list failed: %s", str(e))
        return {"error": f"Failed to extract shopping list: {str(e)}", "items": []}
