import sys
import os
import json

# Add backend directory to sys.path
backend_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.append(backend_dir)

from services.rag.retriever import get_chroma_client

def chunk_text(text: str, chunk_size: int = 500) -> list[str]:
    # Simple chunker by words
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i+chunk_size])
        chunks.append(chunk)
    return chunks

def ingest_text(topic_id: str, content: str, source_url: str = ""):
    client = get_chroma_client()
    collection = client.get_or_create_collection(name="aptitude_knowledge")
    
    chunks = chunk_text(content)
    
    ids = []
    metadatas = []
    documents = []
    
    for i, chunk in enumerate(chunks):
        chunk_id = f"{topic_id}_{source_url}_{i}"
        ids.append(chunk_id)
        metadatas.append({"topic_id": topic_id, "source_url": source_url})
        documents.append(chunk)
        
    if ids:
        collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Ingested {len(ids)} chunks for topic '{topic_id}'")

if __name__ == "__main__":
    # Example usage for the vertical slice
    sample_content = """
    A percentage is a number or ratio expressed as a fraction of 100. 
    It is often denoted using the percent sign, %. 
    To calculate a percentage of a number, multiply the number by the percentage fraction.
    For example, 20% of 150 is (20/100) * 150 = 30.
    
    When a number increases by a percentage, the new value is:
    New Value = Original Value * (1 + Percentage Increase)
    For example, if 50 increases by 10%, the new value is 50 * (1 + 0.10) = 55.
    
    When a number decreases by a percentage, the new value is:
    New Value = Original Value * (1 - Percentage Decrease)
    For example, if 80 decreases by 25%, the new value is 80 * (1 - 0.25) = 60.
    """
    
    print("Ingesting sample data for 'percentages'...")
    ingest_text("percentages", sample_content, "sample_math_book")
