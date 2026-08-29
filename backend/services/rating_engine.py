import math

K_FACTOR = 24

def get_difficulty_rating(difficulty_level: int) -> int:
    """
    Maps 0-10 difficulty to Elo rating (e.g., 0->900, 10->2400)
    Assuming a linear map: rating = 900 + (difficulty_level * 150)
    """
    return 900 + (difficulty_level * 150)

def compute_new_rating(
    current_rating: int,
    difficulty_level: int,
    is_correct: bool,
    used_hint: bool,
    time_taken_ms: int,
    median_time_ms: int = 30000
) -> int:
    """
    Computes the new Reasoning Rating after a question is answered.
    """
    question_rating = get_difficulty_rating(difficulty_level)
    
    # Expected score formula (Elo)
    expected_score = 1 / (1 + math.pow(10, (question_rating - current_rating) / 400))
    
    # Actual score
    if is_correct:
        actual_score = 0.8 if used_hint else 1.0
    else:
        actual_score = 0.0
        
    # Base delta
    delta = K_FACTOR * (actual_score - expected_score)
    
    # Time factor bonus/penalty (±10% max)
    # If time_taken < median_time, factor > 1 (bonus)
    # If time_taken > median_time, factor < 1 (penalty)
    if is_correct and not used_hint and median_time_ms > 0:
        ratio = median_time_ms / max(time_taken_ms, 1000) # prevent div by zero
        # Limit ratio impact
        if ratio > 2.0:
            ratio = 2.0
        if ratio < 0.5:
            ratio = 0.5
            
        # Scale ratio to a ±10% multiplier on the positive delta
        # If ratio = 2.0 (half the time), multiplier = 1.10
        # If ratio = 0.5 (double time), multiplier = 0.90
        # Formula: 1.0 + (ratio - 1.0) * 0.1
        time_multiplier = 1.0 + (ratio - 1.0) * 0.1
        delta = delta * time_multiplier
        
    new_rating = int(round(current_rating + delta))
    return max(0, new_rating) # Rating shouldn't be negative
