import uuid

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from backend.settings import settings


class QdrantService:
    def __init__(self):
        self.qdrant_client = QdrantClient(
            url=settings.QDRANT_DATABASE_URL,
            api_key=settings.QDRANT_API_KEY,
        )
        self.openai_client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
        )

    def vectorize(self, text: str) -> list[float]:
        response = self.openai_client.embeddings.create(
            input=text,
            model="text-embedding-3-small",
        )
        return response.data[0].embedding

    def batch_vectorize(self, texts: list[str]) -> list[list[float]]:
        response = self.openai_client.embeddings.create(
            input=texts,
            model="text-embedding-3-small",
        )
        return [item.embedding for item in response.data]

    def similarity_search(self, text: str, collection_name: str, top_k: int = 5) -> list[dict]:
        vector = self.vectorize(text)
        search_result = self.qdrant_client.query_points(
            collection_name=collection_name,
            query=vector,
            with_payload=True,
            limit=top_k,
        )
        return [
            {
                "id": point.id,
                "score": point.score,
                "payload": point.payload,
            }
            for point in search_result.points
        ]


# Test code
if __name__ == "__main__":
    qdrant_service = QdrantService()

    texts = [
        "eggs",
        "bacon",
        "tomatoes",
        "chocolate",
    ]

    # vectors = qdrant_service.batch_vectorize(texts)
    # points = [
    #     PointStruct(id=str(uuid.uuid4()), vector=vector, payload={"text": text})
    #     for text, vector in zip(texts, vectors)
    # ]

    # Create sample collection (my_collection) and add points before running this test
    # qdrant_service.qdrant_client.create_collection(
    #     collection_name="test_collection",
    #     vectors_config=VectorParams(size=len(vectors[0]), distance=Distance.COSINE),
    # )

    # operation_info = qdrant_service.qdrant_client.upsert(
    #     collection_name="test_collection",
    #     wait=True,
    #     points=points,
    # )

    results = qdrant_service.similarity_search(
        text="sausage",
        collection_name="test_collection",
        top_k=3,
    )
    for result in results:
        print(result)
