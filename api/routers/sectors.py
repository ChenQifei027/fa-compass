# api/routers/sectors.py
import json
import os
from dotenv import load_dotenv
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "data/fa_matching.db")

from core.database import init_db, get_sector, upsert_sector
import core.sector_glossary as sg
from api.jobs import create_job, set_running, set_done, set_failed

init_db(DB_PATH)
router = APIRouter(prefix="/api/sectors")


def _serialize(row: dict) -> dict:
    """把存库的 JSON 字符串字段解出来再返给前端。"""
    return {
        "name": row["name"],
        "description": row.get("description", "") or "",
        "industry_overview": row.get("industry_overview", "") or "",
        "top_companies": json.loads(row.get("top_companies") or "[]"),
        "synonyms": json.loads(row.get("synonyms") or "[]"),
        "generated_at": row.get("generated_at", ""),
        "generated_by": row.get("generated_by", ""),
    }


def _run_generate(job_id: str, name: str):
    set_running(job_id)
    try:
        data = sg.generate_sector_explanation(name)
        upsert_sector(
            DB_PATH, name,
            description=data["description"],
            industry_overview=data["industry_overview"],
            top_companies=json.dumps(data["top_companies"], ensure_ascii=False),
            synonyms=json.dumps(data["synonyms"], ensure_ascii=False),
            generated_by=os.getenv("LLM_MODEL", ""),
        )
        set_done(job_id, {"name": name})
    except Exception as e:
        set_failed(job_id, str(e))


@router.get("/{name}")
def read_sector(name: str):
    row = get_sector(DB_PATH, name)
    if not row:
        raise HTTPException(status_code=404, detail="Sector not generated yet")
    return _serialize(row)


@router.post("/{name}", status_code=202)
def create_sector(name: str, background_tasks: BackgroundTasks,
                  force: bool = Query(False)):
    existing = get_sector(DB_PATH, name)
    if existing and not force:
        raise HTTPException(
            status_code=409,
            detail="Sector already generated; pass ?force=true to regenerate"
        )
    job_id = create_job()
    background_tasks.add_task(_run_generate, job_id, name)
    return {"job_id": job_id, "name": name}
