from fastapi import APIRouter, HTTPException
from api.jobs import get_job

router = APIRouter(prefix="/api/jobs")

@router.get("/{job_id}")
def poll_job(job_id: str):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
