import json
from models.db import get_db_connection

def calculate_mastery(attempts: list[dict]) -> float:
    """
    Calculate mastery score based on recent attempts using exponential decay.
    attempts: list of dicts with 'was_correct' (1 or 0), ordered by oldest to newest.
    We only consider the last 15 attempts.
    """
    recent = attempts[-15:]
    if not recent:
        return 0.0
        
    decay_factor = 0.85 # The further back, the less weight
    total_weight = 0.0
    weighted_score = 0.0
    
    # Iterate from newest to oldest
    for i, attempt in enumerate(reversed(recent)):
        weight = decay_factor ** i
        total_weight += weight
        weighted_score += attempt['was_correct'] * weight
        
    return weighted_score / total_weight if total_weight > 0 else 0.0

def evaluate_topic_unlocks(conn):
    """
    Update topic statuses based on prerequisite mastery.
    """
    cursor = conn.cursor()
    
    # Get all topics and their current progress
    cursor.execute("""
        SELECT t.id, t.prerequisites, p.status, p.mastery_score, p.attempts
        FROM topics t
        LEFT JOIN progress p ON t.id = p.topic_id
    """)
    topics = cursor.fetchall()
    
    # Create a map for quick lookup
    mastery_map = {}
    for row in topics:
        is_mastered = (row['mastery_score'] >= 0.8 and row['attempts'] >= 10)
        mastery_map[row['id']] = is_mastered
        
        if is_mastered and row['status'] != 'mastered':
            cursor.execute("UPDATE progress SET status = 'mastered' WHERE topic_id = ?", (row['id'],))
            
    # Check unlocks
    for row in topics:
        if row['status'] == 'locked':
            prereqs = json.loads(row['prerequisites']) if row['prerequisites'] else []
            # Unlock if all prereqs are mastered
            if all(mastery_map.get(p, False) for p in prereqs):
                cursor.execute("UPDATE progress SET status = 'current' WHERE topic_id = ?", (row['id'],))
                
    conn.commit()

def record_attempt(topic_id: str, question_id: int, was_correct: bool, time_taken: int):
    """
    Record an attempt and update mastery.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Insert attempt
    cursor.execute(
        "INSERT INTO attempts (question_id, topic_id, was_correct, time_taken_seconds) VALUES (?, ?, ?, ?)",
        (question_id, topic_id, 1 if was_correct else 0, time_taken)
    )
    
    # 2. Recalculate mastery
    cursor.execute("SELECT was_correct FROM attempts WHERE topic_id = ? ORDER BY answered_at ASC", (topic_id,))
    all_attempts = [{'was_correct': row['was_correct']} for row in cursor.fetchall()]
    
    new_mastery = calculate_mastery(all_attempts)
    total_attempts = len(all_attempts)
    correct_attempts = sum(a['was_correct'] for a in all_attempts)
    
    cursor.execute(
        """
        UPDATE progress 
        SET mastery_score = ?, attempts = ?, correct = ?, last_practiced_at = CURRENT_TIMESTAMP
        WHERE topic_id = ?
        """,
        (new_mastery, total_attempts, correct_attempts, topic_id)
    )
    
    # 3. Evaluate unlocks in case this pushed us to mastery
    evaluate_topic_unlocks(conn)
    
    conn.commit()
    conn.close()
    
    return new_mastery
