import json
import random
from services.llm.client import generate
from services.math_validator import validate_math_answer

SYSTEM_PROMPT = """
You are a world-class aptitude teacher, teaching one specific student you know well.
Keep explanations concise but complete. No fluff, no filler encouragement, no emoji.
"""

async def generate_practice_question(topic_id: str, mastery_score: float, context: str = "") -> dict:
    """
    Generate a multiple-choice practice question for the given topic.
    Returns a dict with question_text, options, correct_answer, explanation.
    """
    difficulty_context = "basic" if mastery_score < 0.5 else "intermediate" if mastery_score < 0.8 else "advanced"
    
    prompt = f"""
    Generate a single multiple-choice aptitude question on the topic of '{topic_id}'.
    The difficulty should be {difficulty_context}.
    Student's current mastery on this topic: {mastery_score}
    Grounding context: {context or "none — use your own knowledge"}
    
    Provide the response strictly as a JSON object with the following keys:
    "question_text": The question string
    "options": A list of exactly 4 strings, representing the choices (e.g. ["A) 10", "B) 20", "C) 30", "D) 40"])
    "correct_answer": The exact string of the correct option (e.g. "B) 20")
    "explanation": A concise, step-by-step explanation of how to solve it.
    """
    
    try:
        response_text = await generate(
            prompt=prompt,
            system=SYSTEM_PROMPT,
            options={"temperature": 0.3}
        )
        
        # Clean up in case LLM added markdown block
        clean_text = response_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:-3]
        elif clean_text.startswith("```"):
            clean_text = clean_text[3:-3]
            
        data = json.loads(clean_text.strip())
        
        # Basic validation
        if not all(k in data for k in ["question_text", "options", "correct_answer", "explanation"]):
            raise ValueError("Missing keys in LLM JSON response")
            
        return data
        
    except Exception as e:
        print(f"Error generating question: {e}")
        # Fallback question for 'percentages' vertical slice if LLM fails
        return {
            "question_text": "What is 20% of 150?",
            "options": ["A) 20", "B) 30", "C) 40", "D) 50"],
            "correct_answer": "B) 30",
            "explanation": "20% is equal to 20/100 or 1/5. 1/5 of 150 is 30."
        }
