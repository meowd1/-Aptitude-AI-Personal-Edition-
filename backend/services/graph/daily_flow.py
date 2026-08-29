from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from .state import LessonState
from .nodes import (
    retrieve_node,
    teach_node,
    generate_question_node,
    validate_node,
    present_node,
    score_node
)
from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "data" / "lesson_state.db"

def create_daily_flow_graph():
    graph = StateGraph(LessonState)
    
    # Add nodes
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("teach", teach_node)
    graph.add_node("generate_q", generate_question_node)
    graph.add_node("validate", validate_node)
    graph.add_node("present", present_node)
    graph.add_node("score", score_node)
    
    # Edges
    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "teach")
    graph.add_edge("teach", "generate_q")
    graph.add_edge("generate_q", "validate")
    
    graph.add_conditional_edges(
        "validate",
        lambda s: "present" if s.get("valid", False) else "generate_q"
    )
    
    graph.add_edge("present", "score")
    
    graph.add_conditional_edges(
        "score",
        lambda s: "generate_q" if s.get("stage_incomplete", False) else END
    )
    
    # SqliteSaver checkpointer
    # For a real implementation we pass a connection
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    checkpointer = SqliteSaver(conn)
    
    compiled = graph.compile(checkpointer=checkpointer)
    return compiled

# compiled_graph = create_daily_flow_graph()
