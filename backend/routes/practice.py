from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from models.db import get_db_connection
from services.question_engine import generate_practice_question
from services.learning_engine import record_attempt
from services.revision_engine import log_mistake

router = APIRouter(prefix="/practice", tags=["Practice"])

class AnswerSubmission(BaseModel):
    topic_id: str
    question_id: int
    selected_option: str
    time_taken_seconds: int

@router.post("/next")
async def get_next_question(topic_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check current mastery
    cursor.execute("SELECT mastery_score FROM progress WHERE topic_id = ?", (topic_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Topic progress not found")
        
    mastery = row['mastery_score']
    
    # Generate question
    question_data = await generate_practice_question(topic_id, mastery)
    
    # Save to db
    cursor.execute(
        """
        INSERT INTO questions (topic_id, source, difficulty, question_text, options, correct_answer, explanation)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (topic_id, 'generated', 5, question_data['question_text'], 
         ','.join(question_data['options']), question_data['correct_answer'], question_data['explanation'])
    )
    question_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        "id": question_id,
        "topic_id": topic_id,
        "question_text": question_data['question_text'],
        "options": question_data['options']
    }

@router.post("/answer")
def submit_answer(sub: AnswerSubmission):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify answer
    cursor.execute("SELECT correct_answer, explanation FROM questions WHERE id = ?", (sub.question_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Question not found")
        
    correct_answer = row['correct_answer']
    explanation = row['explanation']
    was_correct = (sub.selected_option.strip() == correct_answer.strip())
    
    # Record attempt
    new_mastery = record_attempt(sub.topic_id, sub.question_id, was_correct, sub.time_taken_seconds)
    
    # If wrong, log mistake
    if not was_correct:
        log_mistake(sub.topic_id, sub.question_id)
        
    conn.close()
    
    return {
        "correct": was_correct,
        "correct_answer": correct_answer,
        "explanation": explanation,
        "new_mastery": new_mastery
    }
