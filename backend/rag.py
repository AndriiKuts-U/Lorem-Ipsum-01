import json
import logging
import uuid
from pathlib import Path
from typing import Any

from openai import OpenAI
from qdrant_client.models import PointStruct

from backend.agent_ai import agent
from backend.maps.address import find_nearby_places as _find_nearby_places
from backend.settings import settings


class RAGSystem:
    def __init__(self, collection_name: str = "groceries", memory_dir: str = "./thread_memory"):
        """
        Initialize RAG system with OpenAI, Qdrant, and local memory.

        Args:
            openai_api_key: OpenAI API key
            qdrant_url: Qdrant server URL (default: localhost)
            collection_name: Name of the Qdrant collection
            memory_dir: Directory to store conversation threads
        """

        self.collection_name = collection_name
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        # Initialize collection if it doesn't exist
        # self._init_collection()

    # def _init_collection(self):
    #     """Initialize Qdrant collection for storing document embeddings."""
    # collections = self.qdrant.get_collections().collections
    # collection_exists = any(c.name == self.collection_name for c in collections)

    # if not collection_exists:
    #     self.qdrant.create_collection(
    #         collection_name=self.collection_name,
    #         vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
    #     )
    #     print(f"Created collection: {self.collection_name}")

    def _get_embedding(self, text: str) -> list[float]:
        """Get embedding vector for text using OpenAI embeddings via Pydantic AI's model."""
        # For embeddings we still use OpenAI directly through qdrant workflows; keep existing model name.
        # If desired, switch to pydantic-ai embeddings helper when available.

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.embeddings.create(model="text-embedding-3-small", input=text)
        return response.data[0].embedding

    def add_documents(self, documents: list[dict[str, Any]]):
        """
        Add documents to Qdrant collection.
        """
        points = []
        for doc in documents:
            text = doc.get("text", "")
            metadata = doc.get("metadata", {})

            embedding = self._get_embedding(text)

            point = PointStruct(
                id=str(uuid.uuid4()), vector=embedding, payload={"text": text, **metadata}
            )
            # print(point)
            points.append(point)
            self.qdrant.upsert(collection_name=self.collection_name, points=[point])
        print(f"Added {len(documents)} documents to collection")

    def _load_thread(self, thread_id: str) -> list[dict]:
        """Load conversation thread from local storage."""
        thread_file = self.memory_dir / f"{thread_id}.json"
        if thread_file.exists():
            with open(thread_file, "r") as f:
                return json.load(f)
        return []

    def _save_thread(self, thread_id: str, messages: list[dict]):
        """Save conversation thread to local storage."""
        thread_file = self.memory_dir / f"{thread_id}.json"
        with open(thread_file, "w") as f:
            json.dump(messages, f, indent=2)

    def list_threads(self) -> list[str]:
        """list all available thread IDs."""
        return [f.stem for f in self.memory_dir.glob("*.json")]

    def delete_thread(self, thread_id: str):
        """Delete a conversation thread."""
        thread_file = self.memory_dir / f"{thread_id}.json"
        if thread_file.exists():
            thread_file.unlink()
            print(f"Deleted thread: {thread_id}")

    async def chat_async(
        self,
        query: str,
        thread_id: str | None = None,
    ) -> dict:
        if thread_id is None:
            print("Warning: No thread_id provided; generating a new one.")
            thread_id = str(uuid.uuid4())

        messages = self._load_thread(thread_id)
        history_text = "\n\n".join(
            f"{m.get('role', 'user').capitalize()}: {m.get('content', '')}" for m in messages
        )
        # Enrich the very first user message with nearby stores (pre-tool behavior)
        # Determine location from thread_data or default fallback
        td_dir = Path("./thread_data")
        td_dir.mkdir(parents=True, exist_ok=True)
        td_file = td_dir / f"{thread_id}.json"

        lat: float | None = None
        lng: float | None = None
        radius_m: int | None = None
        try:
            if td_file.exists():
                with td_file.open("r", encoding="utf-8") as fh:
                    d = json.load(fh)
                if "lat" in d and "lng" in d:
                    lat = float(d["lat"])  # type: ignore[index]
                    lng = float(d["lng"])  # type: ignore[index]
                    radius_m = int(d.get("radius_m", 2000))
        except Exception:
            lat = lng = None

        # Fallback to defaults when location is not provided by frontend
        if lat is None or lng is None:
            print("Location data not found; using default coordinates.")
            lat = 48.7318664
            lng = 21.2431019
            radius_m = 2000 if radius_m is None else radius_m
            logging.getLogger(__name__).warning(
                "Location not set for thread %s; using default coordinates (48.7318664, 21.2431019)",
                thread_id,
            )
            try:
                minimal = {"lat": lat, "lng": lng, "radius_m": radius_m}
                if td_file.exists():
                    with td_file.open("r", encoding="utf-8") as fh:
                        prev = json.load(fh)
                    if isinstance(prev, dict):
                        minimal.update(prev)
                with td_file.open("w", encoding="utf-8") as fh:
                    json.dump(minimal, fh)
            except Exception as e:
                print(f"Error occurred while saving thread data: {e}")
                pass

        user_content = query
        if not messages:  # first turn in this thread (with location from thread_data or default)
            try:
                places = _find_nearby_places(
                    lat,
                    lng,
                    radius_m=int(radius_m or 2000),
                    place_types=["supermarket"],
                    max_per_brand=1,
                )
                # Persist full places for frontend usage
                snapshot: dict[str, Any] = {
                    "lat": lat,
                    "lng": lng,
                    "radius_m": radius_m,
                }
                try:
                    if td_file.exists():
                        with td_file.open("r", encoding="utf-8") as fh:
                            prev = json.load(fh)
                        if isinstance(prev, dict):
                            snapshot.update(prev)
                except Exception as e:
                    print(f"Error occurred while loading previous thread data: {e}")
                    pass

                snapshot["places"] = places
                try:
                    with td_file.open("w", encoding="utf-8") as fh:
                        json.dump(snapshot, fh)
                except Exception as e:
                    print(f"Error occurred while saving thread data: {e}")
                    pass

                top = places[:5]
                if top:
                    summary = ", ".join(f"{p['name']} ({p['distance_m']} m)" for p in top)
                    user_content = f"{query}\n\nNearby stores: {summary}."

            except Exception as e:
                print(f"Error occurred while finding nearby places: {e}")
                # Fail-soft: if lookup fails, proceed without enrichment
                user_content = str(e)

        prompt_parts: list[str] = []
        if history_text:
            prompt_parts.append("Conversation so far:\n" + history_text)
        # if context_text:
        #     prompt_parts.append(
        #         context_text
        #         + "\nUse the above context to answer the user's question when relevant."
        #     )
        prompt_parts.append("User: " + user_content)
        agent_input = "\n\n".join(prompt_parts)

        # Run the agent without relying on a nearby-search tool (we already enriched the message)
        result = await agent.run(agent_input)

        assistant_message = str(result.output)
        messages.append({"role": "user", "content": user_content})
        messages.append({"role": "assistant", "content": assistant_message})
        self._save_thread(thread_id, messages)

        return {
            "response": assistant_message,
            "thread_id": thread_id,
            # "retrieved_context": retrieved_docs,
        }
