import json
import os
import sys

# Add backend directory to sys.path so we can import from models
backend_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.append(backend_dir)

from models.db import get_db_connection, init_db

ROADMAP_PATH = os.path.join(backend_dir, "content", "roadmap.json")

def seed_roadmap():
    # Initialize schema first
    init_db()
    
    with open(ROADMAP_PATH, 'r') as f:
        topics = json.load(f)
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for topic in topics:
        prereqs = json.dumps(topic.get('prerequisites', []))
        cursor.execute(
            """
            INSERT OR REPLACE INTO topics (id, name, category, prerequisites, order_index)
            VALUES (?, ?, ?, ?, ?)
            """,
            (topic['id'], topic['name'], topic['category'], prereqs, topic.get('order_index', 0))
        )
        
        # Insert a default locked progress row if not exists
        cursor.execute(
            """
            INSERT OR IGNORE INTO progress (topic_id, status)
            VALUES (?, 'locked')
            """,
            (topic['id'],)
        )
        
    conn.commit()
    conn.close()
    print("Seeded roadmap successfully.")

if __name__ == "__main__":
    seed_roadmap()
