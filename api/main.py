import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import jobs, projects, institutions

app = FastAPI(title="FA Matching API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(jobs.router)
app.include_router(projects.router)
app.include_router(institutions.router)

@app.get("/api/health")
def health():
    return {"status": "ok"}
