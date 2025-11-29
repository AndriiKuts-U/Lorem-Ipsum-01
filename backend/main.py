# RAG System with OpenAI, Qdrant, and Local Thread Memory

import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from settings import Settings
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

settings = Settings()

# FastAPI app
app = FastAPI(
    title="RAG System API",
    description="API for RAG system with OpenAI, Qdrant, and conversation memory",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class Document(BaseModel):
    text: str = Field(..., description="Document text content")
    metadata: Optional[Dict[str, str]] = Field(default_factory=dict, description="Optional metadata")

class AddDocumentsRequest(BaseModel):
    documents: List[Document] = Field(..., description="List of documents to add")

class AddDocumentsResponse(BaseModel):
    message: str
    count: int

class ChatRequest(BaseModel):
    query: str = Field(..., description="User query")
    thread_id: Optional[str] = Field(None, description="Thread ID for conversation continuity")
    use_retrieval: bool = Field(True, description="Whether to use document retrieval")
    top_k: int = Field(3, description="Number of documents to retrieve")

class RetrievedDocument(BaseModel):
    text: str
    score: float

class ChatResponse(BaseModel):
    response: str
    thread_id: str
    retrieved_context: List[RetrievedDocument]

class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    top_k: int = Field(3, description="Number of results to return")

class SearchResponse(BaseModel):
    results: List[RetrievedDocument]

class ThreadListResponse(BaseModel):
    threads: List[str]

class DeleteThreadResponse(BaseModel):
    message: str
    thread_id: str


class RAGSystem:
    def __init__(
            self,
            collection_name: str = "test_collection",
            memory_dir: str = "./thread_memory"
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
        self.qdrant = QdrantClient(url=settings.QDRANT_DATABASE_URL, api_key=settings.QDRANT_API_KEY)
        self.collection_name = collection_name
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)

        # Initialize collection if it doesn't exist
        self._init_collection()

    def _init_collection(self):
        """Initialize Qdrant collection for storing document embeddings."""
        collections = self.qdrant.get_collections().collections
        # collection_exists = any(c.name == self.collection_name for c in collections)

        # if not collection_exists:
        #     self.qdrant.create_collection(
        #         collection_name=self.collection_name,
        #         vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
        #     )
        #     print(f"Created collection: {self.collection_name}")

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding vector for text using OpenAI."""
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    def add_documents(self, documents: List[Dict[str, str]]):
        """
        Add documents to Qdrant collection.

        Args:
            documents: List of dicts with 'text' and optional 'metadata'
        """
        points = []
        for idx, doc in enumerate(documents):
            text = doc.get('text', '')
            metadata = doc.get('metadata', {})

            embedding = self._get_embedding(text)

            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={"text": text, **metadata}
            )
            points.append(point)

        self.qdrant.upsert(
            collection_name=self.collection_name,
            points=points
        )
        print(f"Added {len(documents)} documents to collection")

    def retrieve_context(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Retrieve relevant documents from Qdrant.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of relevant documents with scores
        """
        query_embedding = self._get_embedding(query)

        results = self.qdrant.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=top_k
        )
        print(results)
        return [
            {
                "text": hit.payload["text"],
                "score": hit.score,
                # "metadata": {k: v for k, v in hit.payload.items() if k != "text"}
            }
            for hit in results.points
        ]

    def _load_thread(self, thread_id: str) -> List[Dict]:
        """Load conversation thread from local storage."""
        thread_file = self.memory_dir / f"{thread_id}.json"
        if thread_file.exists():
            with open(thread_file, 'r') as f:
                return json.load(f)
        return []

    def _save_thread(self, thread_id: str, messages: List[Dict]):
        """Save conversation thread to local storage."""
        thread_file = self.memory_dir / f"{thread_id}.json"
        with open(thread_file, 'w') as f:
            json.dump(messages, f, indent=2)

    def chat(
            self,
            query: str,
            thread_id: Optional[str] = None,
            use_retrieval: bool = True,
            top_k: int = 3
    ) -> Dict:
        """
        Chat with the RAG system.

        Args:
            query: User query
            thread_id: Thread ID for conversation memory (creates new if None)
            use_retrieval: Whether to use document retrieval
            top_k: Number of documents to retrieve

        Returns:
            Dict with response, thread_id, and retrieved context
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
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=api_messages
        )

        assistant_message = response.choices[0].message.content

        # Update thread memory
        messages.append({"role": "user", "content": query})
        messages.append({"role": "assistant", "content": assistant_message})
        self._save_thread(thread_id, messages)

        return {
            "response": assistant_message,
            "thread_id": thread_id,
            "retrieved_context": retrieved_docs
        }

    def list_threads(self) -> List[str]:
        """List all available thread IDs."""
        return [f.stem for f in self.memory_dir.glob("*.json")]

    def delete_thread(self, thread_id: str):
        """Delete a conversation thread."""
        thread_file = self.memory_dir / f"{thread_id}.json"
        if thread_file.exists():
            thread_file.unlink()
            print(f"Deleted thread: {thread_id}")


# Global RAG system instance
rag_system: Optional[RAGSystem] = None

@app.on_event("startup")
async def startup_event():
    """Initialize RAG system on startup."""
    global rag_system
    rag_system = RAGSystem()

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "RAG System API is running",
        "version": "1.0.0"
    }


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
        result = rag_system.chat(
            query=request.query,
            thread_id=request.thread_id,
            use_retrieval=request.use_retrieval,
            top_k=request.top_k
        )
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/documents", response_model=AddDocumentsResponse, tags=["Documents"])
async def add_documents_endpoint(request: AddDocumentsRequest):
    """
    Add documents to the vector database.

    - **documents**: List of documents with text and optional metadata
    """
    try:
        # Convert Pydantic models to dicts
        docs = [doc.model_dump() for doc in request.documents]
        rag_system.add_documents(docs)
        return AddDocumentsResponse(
            message="Documents added successfully",
            count=len(request.documents)
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
        results = rag_system.retrieve_context(
            query=request.query,
            top_k=request.top_k
        )
        return SearchResponse(
            results=[RetrievedDocument(**doc) for doc in results]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/threads", response_model=ThreadListResponse, tags=["Threads"])
async def list_threads_endpoint():
    """
    Get a list of all conversation threads.
    """
    try:
        threads = rag_system.list_threads()
        return ThreadListResponse(threads=threads)
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
        thread_file = rag_system.memory_dir / f"{thread_id}.json"
        if not thread_file.exists():
            raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")

        rag_system.delete_thread(thread_id)
        return DeleteThreadResponse(
            message="Thread deleted successfully",
            thread_id=thread_id
        )
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
        messages = rag_system._load_thread(thread_id)
        if not messages:
            raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found or is empty")

        return {
            "thread_id": thread_id,
            "messages": messages,
            "message_count": len(messages)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Run with: uvicorn new_rag:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)