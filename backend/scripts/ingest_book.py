import argparse
import sys
from pathlib import Path

# Add backend dir to python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from services.llm.client import get_embeddings
import os

CHROMA_DIR = BASE_DIR / "data" / "chroma"

def ingest(book_name: str, pdf_path: str):
    print(f"Loading {pdf_path}...")
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()

    # We could do a basic Chapter/Section heuristic detection here
    # For now we tag them generally
    for doc in docs:
        doc.metadata["book"] = book_name
        # Simple heuristic for page number
        doc.metadata["page_number"] = doc.metadata.get("page", 0)

    print(f"Loaded {len(docs)} pages. Splitting...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    chunks = text_splitter.split_documents(docs)
    
    print(f"Created {len(chunks)} chunks. Embedding and saving to Chroma...")
    embeddings = get_embeddings()
    collection_name = f"book_{book_name}"
    
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=collection_name,
        persist_directory=str(CHROMA_DIR)
    )
    
    print(f"Successfully ingested {book_name} into {collection_name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest a PDF book into ChromaDB")
    parser.add_argument("--book", type=str, required=True, help="Book identifier (e.g. aptitude_math or puzzles)")
    parser.add_argument("--path", type=str, required=True, help="Path to the PDF file")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.path):
        print(f"Error: File {args.path} not found.")
        sys.exit(1)
        
    ingest(args.book, args.path)
