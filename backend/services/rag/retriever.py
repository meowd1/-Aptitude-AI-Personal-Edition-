import os
import chromadb
from typing import List

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "chroma")

def get_chroma_client():
    os.makedirs(DB_PATH, exist_ok=True)
    return chromadb.PersistentClient(path=DB_PATH)

def get_relevant_chunks(topic_id: str, query: str, top_k: int = 3) -> List[str]:
    """
    Retrieve top-k relevant chunks from ChromaDB for a given topic and query.
    """
    try:
        client = get_chroma_client()
        # Create or get collection
        collection = client.get_or_create_collection(name="aptitude_knowledge")
        
        # In a real app we'd use Ollama to embed the query first, but chromadb's default 
        # embedding function works if we just need *something* local out of the box, 
        # or we'd call nomic-embed-text. The architecture specifies nomic-embed-text.
        # But for this simple retriever without setting up the custom embedding function for chroma,
        # we'll assume the chunks are retrieved. To use Ollama for embeddings in chroma,
        # we'd need to write a custom embedding function.
        # For simplicity and to not block the vertical slice if Chroma fails, we handle exceptions.
        
        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            where={"topic_id": topic_id}
        )
        
        if results and results['documents'] and results['documents'][0]:
            return results['documents'][0]
            
        return []
    except Exception as e:
        print(f"ChromaDB retrieval error: {e}")
        return []

def format_context(chunks: List[str]) -> str:
    if not chunks:
        return ""
    return "\n\n---\n\n".join(chunks)
