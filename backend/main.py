import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.maps.address import find_nearby_places
from backend.rag import RAGSystem
from backend.rag_tools import GroceryPriceComparer


# Pydantic models for request/response
class Document(BaseModel):
    text: str = Field(..., description="Document text content")
    metadata: dict = Field(default_factory=dict, description="Optional metadata")


class ComparePricesRequest(BaseModel):
    query: str = Field(..., description="Slovak text query (e.g., 'mlieko', 'chlieb')")
    top_k: int = Field(10, description="Number of results to search")
    price_threshold: float = Field(5.0, description="Price difference threshold in percentage")


class ShoppingListRequest(BaseModel):
    items: list[str] = Field(..., description="List of Slovak product queries")
    price_threshold: float = Field(5.0, description="Price difference threshold in percentage")




class AddDocumentsRequest(BaseModel):
    documents: list[Document] = Field(..., description="list of documents to add")


class AddDocumentsResponse(BaseModel):
    message: str
    count: int


class ChatRequest(BaseModel):
    query: str = Field(..., description="User query")
    thread_id: str | None = Field(None, description="Thread ID for conversation continuity")
    use_retrieval: bool = Field(True, description="Whether to use document retrieval")
    top_k: int = Field(3, description="Number of documents to retrieve")


class RetrievedDocument(BaseModel):
    text: str
    score: float


class ChatResponse(BaseModel):
    response: str
    thread_id: str
    # retrieved_context: list[RetrievedDocument]


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    top_k: int = Field(3, description="Number of results to return")


class SearchResponse(BaseModel):
    results: list[RetrievedDocument]


class ThreadlistResponse(BaseModel):
    threads: list[str]


class DeleteThreadResponse(BaseModel):
    message: str
    thread_id: str


class NearbyPlacesRequest(BaseModel):
    lat: float
    lng: float
    radius_m: int = Field(5000, ge=1, description="Search radius in meters")
    types: list[str] | None = Field(None, description="Google place types to include")
    max_per_brand: int = Field(1, ge=0, description="Cap results per brand; 0 disables")


class NearbyPlace(BaseModel):
    name: str
    lat: float
    lng: float
    distance_m: int
    place_id: str | None = None


class NearbyPlacesResponse(BaseModel):
    places: list[NearbyPlace]


# Session models
class SetLocationRequest(BaseModel):
    thread_id: str
    lat: float
    lng: float
    radius_m: int | None = Field(default=5000, ge=1)


class LocationResponse(BaseModel):
    thread_id: str
    lat: float
    lng: float
    radius_m: int


@asynccontextmanager
async def lifespan(app: FastAPI):
    rag_system = RAGSystem()
    app.state.rag_system = rag_system
    # Run app
    yield
    # Shutdown


# FastAPI app
app = FastAPI(
    title="RAG System API",
    description="API for RAG system with OpenAI, Qdrant, and conversation memory",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {"status": "healthy", "message": "RAG System API is running", "version": "1.0.0"}


# API Endpoints


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat_endpoint(request: ChatRequest):
    """
    Chat with the RAG system.

    - **query**: The user's question or message
    - **thread_id**: Optional thread ID for conversation continuity
    - **use_retrieval**: Whether to retrieve relevant documents from the vector store
    - **top_k**: Number of documents to retrieve (if use_retrieval is True)
    """
    try:
        result = await app.state.rag_system.chat_async(
            query=request.query,
            thread_id=request.thread_id,
            use_retrieval=request.use_retrieval,
            top_k=request.top_k,
        )
        return ChatResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/documents", response_model=AddDocumentsResponse, tags=["Documents"])
async def add_documents_endpoint(request: AddDocumentsRequest):
    """
    Add documents to the vector database.

    - **documents**: list of documents with text and optional metadata
    """
    try:
        # Convert Pydantic models to dicts
        docs = [doc.model_dump() for doc in request.documents]
        # print(docs)
        app.state.rag_system.add_documents(docs)
        return AddDocumentsResponse(
            message="Documents added successfully", count=len(request.documents)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/documents/search", response_model=SearchResponse, tags=["Documents"])
async def search_documents_endpoint(request: SearchRequest):
    """
    Search for relevant documents in the vector database.

    - **query**: The search query
    - **top_k**: Number of results to return
    """
    try:
        results = app.state.rag_system.retrieve_context(query=request.query, top_k=request.top_k)
        return SearchResponse(results=[RetrievedDocument(**doc) for doc in results])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


THREAD_DATA_DIR = Path("./thread_data")
THREAD_DATA_DIR.mkdir(parents=True, exist_ok=True)


@app.post("/session/location", response_model=LocationResponse, tags=["Session"])
async def set_location(request: SetLocationRequest):
    try:
        data = {
            "lat": request.lat,
            "lng": request.lng,
            "radius_m": request.radius_m or 5000,
        }
        f = THREAD_DATA_DIR / f"{request.thread_id}.json"
        with f.open("w", encoding="utf-8") as fh:
            json.dump(data, fh)
        return LocationResponse(
            thread_id=request.thread_id,
            lat=data["lat"],
            lng=data["lng"],
            radius_m=data["radius_m"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session/location/{thread_id}", response_model=LocationResponse, tags=["Session"])
async def get_location(thread_id: str):
    f = THREAD_DATA_DIR / f"{thread_id}.json"
    if not f.exists():
        raise HTTPException(status_code=404, detail="Location not set for thread")
    try:
        with f.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return LocationResponse(
            thread_id=thread_id,
            lat=float(data.get("lat")),
            lng=float(data.get("lng")),
            radius_m=int(data.get("radius_m", 5000)),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/session/location/{thread_id}", response_model=DeleteThreadResponse, tags=["Session"])
async def delete_location(thread_id: str):
    f = THREAD_DATA_DIR / f"{thread_id}.json"
    if f.exists():
        try:
            f.unlink()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    return DeleteThreadResponse(message="Location removed", thread_id=thread_id)


@app.post("/places/nearby", response_model=NearbyPlacesResponse, tags=["Places"])
async def nearby_places_endpoint(request: NearbyPlacesRequest):
    """Return nearby places by Google Places v1 around given coordinates."""
    try:
        places = find_nearby_places(
            request.lat,
            request.lng,
            radius_m=request.radius_m,
            place_types=request.types or ["supermarket"],
            min_unique=20,
            max_pages=5,
            max_per_brand=request.max_per_brand,
        )
        return NearbyPlacesResponse(places=[NearbyPlace(**p) for p in places])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/threads", response_model=ThreadlistResponse, tags=["Threads"])
async def list_threads_endpoint():
    """
    Get a list of all conversation threads.
    """
    try:
        threads = app.state.rag_system.list_threads()
        return ThreadlistResponse(threads=threads)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/threads/{thread_id}", response_model=DeleteThreadResponse, tags=["Threads"])
async def delete_thread_endpoint(thread_id: str):
    """
    Delete a specific conversation thread.

    - **thread_id**: The ID of the thread to delete
    """
    try:
        # Check if thread exists
        thread_file = app.state.rag_system.memory_dir / f"{thread_id}.json"
        if not thread_file.exists():
            raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")

        app.state.rag_system.delete_thread(thread_id)
        return DeleteThreadResponse(message="Thread deleted successfully", thread_id=thread_id)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/threads/{thread_id}", tags=["Threads"])
async def get_thread_endpoint(thread_id: str):
    """
    Get the conversation history for a specific thread.

    - **thread_id**: The ID of the thread to retrieve
    """
    try:
        messages = app.state.rag_system._load_thread(thread_id)
        if not messages:
            raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found or is empty")

        return {"thread_id": thread_id, "messages": messages, "message_count": len(messages)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/prices/compare", tags=["Price Comparison"])
async def compare_prices_endpoint(request: ComparePricesRequest):
    """
    Compare prices for a grocery item across different stores.

    - **query**: Slovak text query (e.g., "mlieko", "chlieb", "maslo")
    - **top_k**: Number of similar items to retrieve
    - **price_threshold**: Price difference threshold in percentage (e.g., 5.0 for 5%)

    Returns price comparison with cheapest store and price differences.
    """
    try:
        comparer = GroceryPriceComparer(
            rag_system=app.state.rag_system,
            price_threshold_percent=request.price_threshold
        )

        result = comparer.compare_prices(query=request.query, top_k=request.top_k)

        if not result:
            raise HTTPException(status_code=404, detail=f"No products found for query: {request.query}")

        # Convert dataclass to dict for JSON response
        return {
            "query": result.query,
            "cheapest_store": result.cheapest_store,
            "cheapest_price": result.cheapest_price,
            "price_differences": result.price_differences,
            "recommendation": result.recommendation,
            "items_count": sum(len(items) for items in result.items_by_store.values()),
            "stores_found": list(result.items_by_store.keys())
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/prices/shopping-list", tags=["Price Comparison"])
async def shopping_list_endpoint(request: ShoppingListRequest):
    """
    Find the best store for buying all items in a shopping list.

    - **items**: List of Slovak product queries (e.g., ["mlieko", "chlieb", "maslo"])
    - **price_threshold**: Price difference threshold in percentage

    Returns analysis of which store is best for your entire shopping list with total savings.
    """
    try:
        comparer = GroceryPriceComparer(
            rag_system=app.state.rag_system,
            price_threshold_percent=request.price_threshold
        )

        result = comparer.get_best_store_for_list(items=request.items)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Run with: python -m uvicorn backend.main:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
