from typing import TypedDict, Optional, List, Dict, Any

class LessonState(TypedDict):
    topic_id: str
    stage: str # learn / guided / independent / mistakes / revision / challenge
    retrieved_chunks: List[Any]
    current_question: Optional[Dict[str, Any]]
    attempts_this_stage: int
    mastery_score: float
    reasoning_rating: int
    stage_incomplete: bool
    valid: bool
