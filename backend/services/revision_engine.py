import datetime
from models.db import get_db_connection

BASE_INTERVALS = [1, 3, 7, 15, 30, 90]

def schedule_next_review(mistake_id: int, was_correct: bool):
    """
    Update spaced repetition schedule based on performance.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT mistake_count, interval_days FROM mistakes WHERE id = ?", (mistake_id,))
    row = cursor.fetchone()
    
    if not row:
        return
        
    mistake_count = row['mistake_count']
    current_interval = row['interval_days']
    
    if was_correct:
        # Move to next interval
        try:
            current_index = BASE_INTERVALS.index(current_interval)
            next_interval = BASE_INTERVALS[min(current_index + 1, len(BASE_INTERVALS) - 1)]
        except ValueError:
            next_interval = BASE_INTERVALS[0]
    else:
        # Reset interval and increment mistake count
        next_interval = BASE_INTERVALS[0]
        mistake_count += 1
        
    next_review_at = datetime.datetime.now() + datetime.timedelta(days=next_interval)
    
    cursor.execute(
        """
        UPDATE mistakes 
        SET mistake_count = ?, interval_days = ?, next_review_at = ?, last_reviewed_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (mistake_count, next_interval, next_review_at, mistake_id)
    )
    
    conn.commit()
    conn.close()

def log_mistake(topic_id: str, question_id: int):
    """
    Log a new mistake or update existing one for a question.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM mistakes WHERE question_id = ?", (question_id,))
    row = cursor.fetchone()
    
    if row:
        schedule_next_review(row['id'], False)
    else:
        next_review = datetime.datetime.now() + datetime.timedelta(days=BASE_INTERVALS[0])
        cursor.execute(
            """
            INSERT INTO mistakes (question_id, topic_id, interval_days, next_review_at)
            VALUES (?, ?, ?, ?)
            """,
            (question_id, topic_id, BASE_INTERVALS[0], next_review)
        )
        
    conn.commit()
    conn.close()
