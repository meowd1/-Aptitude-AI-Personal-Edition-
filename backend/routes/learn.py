from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from services.rag.retriever import get_relevant_chunks, format_context
from services.llm.client import generate_stream
from models.db import get_db_connection
import json

router = APIRouter(prefix="/learn", tags=["Learn"])

SYSTEM_PROMPT = """
You are a world-class aptitude teacher, teaching one specific student you know well.
Teach from first principles. Never assume prior knowledge unless the student's 
mastery data says otherwise.
Always explain step by step. Prefer understanding over memorization.
When teaching, use the grounding context below if provided — stay consistent with it,
but you may expand with your own reasoning and analogies.
Keep explanations concise but complete. No fluff, no filler encouragement, no emoji.
"""

@router.get("/{topic_id}")
async def learn_concept(topic_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get current mastery
    cursor.execute("SELECT mastery_score FROM progress WHERE topic_id = ?", (topic_id,))
    row = cursor.fetchone()
    mastery = row['mastery_score'] if row else 0.0
    conn.close()
    
    # Retrieve context
    chunks = get_relevant_chunks(topic_id, f"Explain the concept of {topic_id}")
    context = format_context(chunks)
    
    prompt = f"""
    Explain the concept of '{topic_id}'.
    Student's current mastery on this topic: {mastery}
    Grounding context: {context or "none — use your own knowledge"}
    """
    
    async def event_generator():
        async for chunk in generate_stream(prompt=prompt, system=SYSTEM_PROMPT, options={"temperature": 0.5}):
            # Send server-sent events
            yield f"data: {json.dumps({'content': chunk})}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")
