import uuid
from typing import Any, Dict, Optional

_jobs: Dict[str, dict] = {}

def create_job() -> str:
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "pending", "result": None, "error": None}
    return job_id

def set_running(job_id: str) -> None:
    _jobs[job_id]["status"] = "running"

def set_done(job_id: str, result: Any) -> None:
    _jobs[job_id].update({"status": "completed", "result": result})

def set_failed(job_id: str, error: str) -> None:
    _jobs[job_id].update({"status": "failed", "error": error})

def get_job(job_id: str) -> Optional[dict]:
    return _jobs.get(job_id)
