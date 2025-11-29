import json
import uuid
from pathlib import Path
from typing import Any

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

from backend.settings import settings


class RAGSystem:
    def __init__(
        self, collection_name: str = "test_collection", memory_dir: str = "./thread_memory"
    ):
        """
        Initialize RAG system with OpenAI, Qdrant, and local memory.

        Args:
            openai_api_key: OpenAI API key
            qdrant_url: Qdrant server URL (default: localhost)
            collection_name: Name of the Qdrant collection
            memory_dir: Directory to store conversation threads
        """
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.qdrant = QdrantClient(
            url=settings.QDRANT_DATABASE_URL, api_key=settings.QDRANT_API_KEY
        )
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
        """Get embedding vector for text using OpenAI."""
        response = self.client.embeddings.create(model="text-embedding-3-small", input=text)
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
            points.append(point)

        self.qdrant.upsert(collection_name=self.collection_name, points=points)
        print(f"Added {len(documents)} documents to collection")

    def retrieve_context(self, query: str, top_k: int = 3) -> list[dict]:
        """Retrieve relevant documents from Qdrant."""

        query_embedding = self._get_embedding(query)

        results = self.qdrant.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=top_k,
            with_payload=True,
        )
        print(results)
        out = []
        for hit in results.points:
            payload = hit.payload or {}
            text_val = payload.get("text", "")
            out.append(
                {
                    "text": text_val,
                    "score": hit.score,
                }
            )
        return out

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

    def chat(
        self,
        query: str,
        thread_id: str | None = None,
        use_retrieval: bool = True,
        top_k: int = 3,
    ) -> dict:
        """
        Chat with the RAG system.
        """
        # Create or load thread
        if thread_id is None:
            thread_id = str(uuid.uuid4())

        messages = self._load_thread(thread_id)

        # Retrieve relevant context if enabled
        context_text = ""
        retrieved_docs = []
        if use_retrieval:
            retrieved_docs = self.retrieve_context(query, top_k=top_k)
            if retrieved_docs:
                context_text = "\n\nRelevant context:\n" + "\n".join(
                    f"- {doc['text']}" for doc in retrieved_docs
                )

        # Build messages for API call
        api_messages = []

        # System message with context
        system_content = "You are a helpful assistant."
        if context_text:
            system_content += f"{context_text}\n\nUse the above context to answer the user's question when relevant."

        api_messages.append({"role": "system", "content": system_content})

        # Add conversation history
        api_messages.extend(messages)

        # Add current query
        api_messages.append({"role": "user", "content": query})

        # Get response from OpenAI
        response = self.client.chat.completions.create(model="gpt-4o-mini", messages=api_messages)

        assistant_message = response.choices[0].message.content

        # Update thread memory
        messages.append({"role": "user", "content": query})
        messages.append({"role": "assistant", "content": assistant_message})
        self._save_thread(thread_id, messages)

        return {
            "response": assistant_message,
            "thread_id": thread_id,
            "retrieved_context": retrieved_docs,
        }

    def list_threads(self) -> list[str]:
        """list all available thread IDs."""
        return [f.stem for f in self.memory_dir.glob("*.json")]

    def delete_thread(self, thread_id: str):
        """Delete a conversation thread."""
        thread_file = self.memory_dir / f"{thread_id}.json"
        if thread_file.exists():
            thread_file.unlink()
            print(f"Deleted thread: {thread_id}")
