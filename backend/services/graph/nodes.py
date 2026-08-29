from .state import LessonState
from langchain_chroma import Chroma
from services.llm.client import get_embeddings, get_llm
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CHROMA_DIR = BASE_DIR / "data" / "chroma"

def get_vectorstore(book_name="aptitude_math"):
    embeddings = get_embeddings()
    return Chroma(
        collection_name=f"book_{book_name}",
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR)
    )

def retrieve_node(state: LessonState) -> LessonState:
    topic_id = state.get("topic_id")
    # For daily challenge, we pull from puzzles
    source = "puzzles" if state.get("stage") == "challenge" else "aptitude_math"
    
    store = get_vectorstore(source)
    # Simple similarity search. In reality, filter by topic_id if possible
    chunks = store.similarity_search(topic_id, k=4)
    
    return {**state, "retrieved_chunks": chunks}

def teach_node(state: LessonState) -> LessonState:
    # Use LLM to explain the concept grounded in chunks
    llm = get_llm()
    # Mocking the actual LLM call for now
    return state

def generate_question_node(state: LessonState) -> LessonState:
    # Use LLM to draft a question
    # Mocking
    state["current_question"] = {
        "text": "Generated mock question for " + state["topic_id"],
        "options": ["A", "B", "C", "D"],
        "correct_answer": "A",
        "explanation": "Mock explanation"
    }
    return state

def validate_node(state: LessonState) -> LessonState:
    # Validate question, e.g., with sympy
    state["valid"] = True
    return state

def present_node(state: LessonState) -> LessonState:
    # Wait for user input via frontend (usually handled via interrupting graph or returning state)
    return state

def score_node(state: LessonState) -> LessonState:
    # Update mastery, Rating, etc
    state["attempts_this_stage"] += 1
    state["stage_incomplete"] = state["attempts_this_stage"] < 3 # e.g. need 3 questions
    return state
