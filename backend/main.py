from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Aptitude AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/user/rating")
def get_user_rating():
    # Mock for frontend
    return {"rating": 1247, "delta_today": 18}

@app.post("/api/session/start")
def start_session():
    # Placeholder for invoking daily flow graph
    return {"status": "started", "session_id": "mock-session-123"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
