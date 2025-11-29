import json

import requests

# Base URL for the API
BASE_URL = "http://localhost:8000"


def health_check():
    """Test the health check endpoint."""
    print("\n" + "=" * 60)
    print("1. HEALTH CHECK")
    print("=" * 60)

    response = requests.get(f"{BASE_URL}/")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()


def add_documents():
    """Add sample documents to the vector database."""
    print("\n" + "="*60)
    print("2. ADD DOCUMENTS")
    print("="*60)

    documents = json.load(open("data/lidl_products_parsed.json", encoding="utf-8"))
    insert_documents = []
    for i in documents:
        insert_documents.append({"text": i["name"],
                                 "metadata": {"source":"lidl",
                                              "price": i["price"],
                                              "price_original": i["price_original"],
                                              # "discount_percentage": i["discount_percentage"],
                                              "amount": i["amount"],
                                              "description": i["description"],
                                              "category": i["category"]
                                              }})


    response = requests.post(f"{BASE_URL}/documents", json={"documents": insert_documents}, timeout=1000000)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()


def search_documents(query: str, top_k: int = 3):
    """Search for relevant documents."""
    print("\n" + "=" * 60)
    print("3. SEARCH DOCUMENTS")
    print("=" * 60)

    search_request = {"query": query, "top_k": top_k}

    print(f"Query: '{query}'")
    response = requests.post(f"{BASE_URL}/documents/search", json=search_request)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()


def chat_without_retrieval(query: str, thread_id: str | None = None):
    """Chat without document retrieval."""
    print("\n" + "=" * 60)
    print("4. CHAT WITHOUT RETRIEVAL")
    print("=" * 60)

    chat_request = {"query": query, "use_retrieval": False}

    if thread_id:
        chat_request["thread_id"] = thread_id

    print(f"Query: '{query}'")
    response = requests.post(f"{BASE_URL}/chat", json=chat_request)
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Thread ID: {result.get('thread_id')}")
    print(f"Response: {result.get('response')}")
    print(f"Retrieved Context: {result.get('retrieved_context')}")
    return result


def chat_with_retrieval(query: str, thread_id: str | None = None, top_k: int = 3):
    """Chat with document retrieval (RAG)."""
    print("\n" + "=" * 60)
    print("5. CHAT WITH RETRIEVAL (RAG)")
    print("=" * 60)

    chat_request = {"query": query, "use_retrieval": True, "top_k": top_k}

    if thread_id:
        chat_request["thread_id"] = thread_id

    print(f"Query: '{query}'")
    response = requests.post(f"{BASE_URL}/chat", json=chat_request)
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Thread ID: {result.get('thread_id')}")
    print(f"Response: {result.get('response')}")
    print(f"\nRetrieved Context ({len(result.get('retrieved_context', []))} documents):")
    for i, doc in enumerate(result.get("retrieved_context", []), 1):
        print(f"  {i}. [Score: {doc['score']:.4f}] {doc['text'][:100]}...")
    return result


def list_threads():
    """List all conversation threads."""
    print("\n" + "=" * 60)
    print("6. LIST THREADS")
    print("=" * 60)

    response = requests.get(f"{BASE_URL}/threads")
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Threads: {result.get('threads')}")
    return result


def get_thread(thread_id: str):
    """Get a specific thread's conversation history."""
    print("\n" + "=" * 60)
    print("7. GET THREAD HISTORY")
    print("=" * 60)

    print(f"Thread ID: {thread_id}")
    response = requests.get(f"{BASE_URL}/threads/{thread_id}")
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Message Count: {result.get('message_count')}")
    print("Messages:")
    for i, msg in enumerate(result.get("messages", []), 1):
        print(f"  {i}. [{msg['role']}]: {msg['content'][:100]}...")
    return result


def delete_thread(thread_id: str):
    """Delete a conversation thread."""
    print("\n" + "=" * 60)
    print("8. DELETE THREAD")
    print("=" * 60)

    print(f"Thread ID: {thread_id}")
    response = requests.delete(f"{BASE_URL}/threads/{thread_id}")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()


def run_full_demo():
    """Run a comprehensive demo of all API endpoints."""
    print("\n" + "#" * 60)
    print("# RAG API COMPREHENSIVE DEMO")
    print("#" * 60)

    try:
        # 1. Health check
        health_check()

        # # 2. Add documents to the vector database
        add_documents()

        # 3. Search for documents
        search_documents("What is Python?", top_k=2)
        search_documents("Tell me about machine learning", top_k=3)

        # 4. Chat without retrieval
        result1 = chat_without_retrieval("Hello! What can you help me with?")
        thread_id = result1["thread_id"]

        # 5. Continue conversation in same thread
        chat_without_retrieval("What's 2+2?", thread_id=thread_id)

        # 6. Chat with retrieval (RAG)
        result2 = chat_with_retrieval("What is Python and why is it popular?")
        rag_thread_id = result2["thread_id"]

        # 7. Continue RAG conversation
        chat_with_retrieval("Can you tell me more about RAG?", thread_id=rag_thread_id)

        # 8. List all threads
        threads_result = list_threads()

        # 9. Get thread history
        if threads_result["threads"]:
            get_thread(threads_result["threads"][0])

        # 10. Delete a thread
        if len(threads_result["threads"]) > 0:
            delete_thread(threads_result["threads"][0])

        # 11. Verify deletion
        list_threads()

        print("\n" + "#" * 60)
        print("# DEMO COMPLETED SUCCESSFULLY!")
        print("#" * 60)

    except requests.exceptions.ConnectionError:
        print("\nL ERROR: Could not connect to the API.")
        print("Make sure the API is running: uvicorn backend.new_rag:app --reload --port 8000")
    except Exception as e:
        print(f"\nL ERROR: {e}")


def interactive_chat():
    """Interactive chat session with RAG."""
    print("\n" + "#" * 60)
    print("# INTERACTIVE RAG CHAT")
    print("#" * 60)
    print("Type 'quit' to exit, 'new' to start a new thread")
    print("Type 'no-rag' to disable retrieval, 'rag' to enable it")
    print("#" * 60)

    thread_id = None
    use_retrieval = True

    while True:
        user_input = input("\n=d You: ").strip()

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print("Goodbye!")
            break

        if user_input.lower() == "new":
            thread_id = None
            print("= Started new conversation thread")
            continue

        if user_input.lower() == "no-rag":
            use_retrieval = False
            print("= Retrieval disabled")
            continue

        if user_input.lower() == "rag":
            use_retrieval = True
            print("= Retrieval enabled")
            continue

        try:
            chat_request = {"query": user_input, "use_retrieval": use_retrieval, "top_k": 3}

            if thread_id:
                chat_request["thread_id"] = thread_id

            response = requests.post(f"{BASE_URL}/chat", json=chat_request)
            result = response.json()

            thread_id = result["thread_id"]

            print(f"\n> Assistant: {result['response']}")

            if use_retrieval and result.get("retrieved_context"):
                print(f"\n=� Retrieved {len(result['retrieved_context'])} relevant documents")

        except requests.exceptions.ConnectionError:
            print("\nL ERROR: Could not connect to the API.")
            print("Make sure the API is running: uvicorn backend.new_rag:app --reload --port 8000")
            break
        except Exception as e:
            print(f"\nL ERROR: {e}")


if __name__ == "__main__":
    # import sys
    #
    # if len(sys.argv) > 1 and sys.argv[1] == "interactive":
    #     interactive_chat()
    # else:
    #     run_full_demo()
    add_documents()
        # Uncomment to run interactive mode after demo
        # print("\n\nStarting interactive mode...")
        # interactive_chat()
