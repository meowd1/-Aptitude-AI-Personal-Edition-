from fastapi import APIRouter
from models.db import get_db_connection
import json

router = APIRouter()

@router.get("/roadmap")
def get_roadmap():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT t.id, t.name, t.category, t.prerequisites, p.status
        FROM topics t
        LEFT JOIN progress p ON t.id = p.topic_id
        ORDER BY t.order_index
    """)
    rows = cursor.fetchall()
    
    roadmap_data = {}
    for row in rows:
        cat = row['category']
        if cat not in roadmap_data:
            roadmap_data[cat] = []
        roadmap_data[cat].append({
            "id": row['id'],
            "name": row['name'],
            "status": row['status'] if row['status'] else "locked",
            "prerequisites": json.loads(row['prerequisites']) if row['prerequisites'] else []
        })
    
    conn.close()
    return roadmap_data
