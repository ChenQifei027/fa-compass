import os, json, tempfile
from pathlib import Path
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from pydantic import BaseModel

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "data/fa_matching.db")
BP_DIR = Path(os.getenv("BP_DIR", "data/bps"))
BROWSER_STATE = os.getenv("BROWSER_STATE", "")

from core.database import (
    init_db, insert_project, list_projects, get_project,
    update_project, delete_project,
    upsert_project_report, insert_funding_round,
    list_funding_rounds, delete_project_funding_rounds,
    upsert_project_research,
)
from core.bp_parser import extract_text_from_file, extract_project_info, extract_report_info
from core.scraper import scrape_company_funding, scrape_sector_companies
from core.researcher import generate_industry_research
from api.jobs import create_job, set_running, set_done, set_failed

init_db(DB_PATH)
router = APIRouter(prefix="/api/projects")

class ProjectIn(BaseModel):
    name: str
    file_path: str = ""
    sector: str = ""
    sub_sector: str = ""
    stage: str = ""
    location: str = ""
    description: str = ""
    highlights: str = ""
    financing_need: str = ""

class ProjectUpdate(BaseModel):
    sector: str = ""
    sub_sector: str = ""
    stage: str = ""
    location: str = ""
    description: str = ""
    highlights: str = ""
    financing_need: str = ""

@router.get("")
def get_projects():
    return list_projects(DB_PATH)

@router.post("", status_code=201)
def create_project(body: ProjectIn):
    pid = insert_project(DB_PATH, **body.model_dump())
    return get_project(DB_PATH, pid)

@router.get("/{project_id}")
def read_project(project_id: int):
    p = get_project(DB_PATH, project_id)
    if not p:
        raise HTTPException(404, "Project not found")
    return p

@router.put("/{project_id}")
def update_project_endpoint(project_id: int, body: ProjectUpdate):
    if not get_project(DB_PATH, project_id):
        raise HTTPException(404, "Project not found")
    update_project(DB_PATH, project_id, **body.model_dump())
    return get_project(DB_PATH, project_id)

@router.delete("/{project_id}", status_code=204)
def remove_project(project_id: int):
    if not get_project(DB_PATH, project_id):
        raise HTTPException(404, "Project not found")
    delete_project(DB_PATH, project_id)

@router.post("/parse")
async def parse_bp(file: UploadFile = File(...)):
    BP_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "file.pdf").suffix
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=BP_DIR)
    try:
        tmp.write(await file.read())
        tmp.flush()
        text = extract_text_from_file(tmp.name)
        info = extract_project_info(text) if text.strip() else {}
        info["file_path"] = tmp.name
        info["default_name"] = Path(file.filename or "").stem
        return info
    finally:
        tmp.close()

def _run_report(job_id: str, project: dict):
    set_running(job_id)
    try:
        bp_text = extract_text_from_file(project["file_path"]) if project.get("file_path") else ""
        report = extract_report_info(bp_text)
        upsert_project_report(DB_PATH, project["id"], json.dumps(report, ensure_ascii=False))
        delete_project_funding_rounds(DB_PATH, project["id"])
        rounds = scrape_company_funding(project["name"], BROWSER_STATE)
        for r in rounds:
            insert_funding_round(DB_PATH, project_id=project["id"], **r)
        set_done(job_id, {"rounds_count": len(rounds)})
    except Exception as e:
        set_failed(job_id, str(e))

@router.post("/{project_id}/report", status_code=202)
def generate_report(project_id: int, background_tasks: BackgroundTasks):
    p = get_project(DB_PATH, project_id)
    if not p:
        raise HTTPException(404, "Project not found")
    job_id = create_job()
    background_tasks.add_task(_run_report, job_id, dict(p))
    return {"job_id": job_id}

def _run_research(job_id: str, project: dict):
    set_running(job_id)
    try:
        keyword = project.get("sub_sector") or project.get("sector") or project["name"]
        companies = scrape_sector_companies(keyword, BROWSER_STATE)
        research = generate_industry_research(project, companies)
        upsert_project_research(DB_PATH, project["id"], json.dumps(research, ensure_ascii=False))
        set_done(job_id, {"ok": True})
    except Exception as e:
        set_failed(job_id, str(e))

@router.post("/{project_id}/research", status_code=202)
def generate_research(project_id: int, background_tasks: BackgroundTasks):
    p = get_project(DB_PATH, project_id)
    if not p:
        raise HTTPException(404, "Project not found")
    job_id = create_job()
    background_tasks.add_task(_run_research, job_id, dict(p))
    return {"job_id": job_id}

@router.get("/{project_id}/funding-rounds")
def get_funding_rounds(project_id: int):
    if not get_project(DB_PATH, project_id):
        raise HTTPException(404, "Project not found")
    return list_funding_rounds(DB_PATH, project_id)
