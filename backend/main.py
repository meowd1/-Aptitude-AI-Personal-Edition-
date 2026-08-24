from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup models and db
from models.db import init_db

app = FastAPI(title="Aptitude AI Backend")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # Attempt to initialize db (will not overwrite data if exists due to IF NOT EXISTS in schema)
    # However, if seed_roadmap was run, we're good.
    pass

@app.get("/")
def read_root():
    return {"status": "ok", "app": "Aptitude AI"}

@app.get("/home")
def get_home():
    return {
        "greeting": _get_greeting(),
        "streak": 12, # mock data for now
        "day_number": 48, # mock data
        "mastery_percentage": 62, # mock data
        "missions": [
            {"id": "learn", "label": "Learn", "done": True},
            {"id": "practice", "label": "Practice", "done": False},
            {"id": "review", "label": "Review Mistakes", "done": False},
            {"id": "revision", "label": "Revision", "done": False}
        ]
    }

def _get_greeting():
    hour = datetime.datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 18:
        return "Good afternoon"
    else:
        return "Good evening"

# Import other routes here as they are created
from routes import roadmap, practice, learn

app.include_router(roadmap.router)
app.include_router(practice.router)
app.include_router(learn.router)
