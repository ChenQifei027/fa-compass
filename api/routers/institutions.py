import os, io
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import pandas as pd

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "data/fa_matching.db")
BROWSER_STATE = os.getenv("BROWSER_STATE_PATH", "data/browser_state.json")

from core.database import (
    init_db, insert_institution, list_institutions, get_institution,
    update_institution, delete_institution,
    insert_investment_record, list_investment_records,
)
from core.scraper import scrape_institution_investments, scrape_event_description
from core.database import list_records_missing_desc, update_investment_record_desc
from api.jobs import create_job, set_running, set_done, set_failed

init_db(DB_PATH)
router = APIRouter(prefix="/api/institutions")

class InstitutionIn(BaseModel):
    name: str
    location: str = ""
    known_preferences: str = ""
    contact_name: str = ""
    contact_wechat: str = ""
    fa_fee_note: str = ""
    response_style: str = ""
    track_updates: int = 1

class InstitutionUpdate(BaseModel):
    location: Optional[str] = None
    known_preferences: Optional[str] = None
    contact_name: Optional[str] = None
    contact_wechat: Optional[str] = None
    fa_fee_note: Optional[str] = None
    response_style: Optional[str] = None
    website: Optional[str] = None
    founded_year: Optional[str] = None
    aum: Optional[str] = None
    current_fund: Optional[str] = None
    key_partners: Optional[str] = None
    preferred_sectors: Optional[str] = None
    preferred_stages: Optional[str] = None
    track_updates: Optional[int] = None

def _scrape(job_id: str, iid: int, name: str):
    set_running(job_id)
    try:
        result = scrape_institution_investments(name, BROWSER_STATE)
        inst_info = {k: v for k, v in result["institution"].items() if v}
        if inst_info:
            update_institution(DB_PATH, iid, **inst_info)
        for r in result["records"]:
            insert_investment_record(DB_PATH, institution_id=iid, **r)
        set_done(job_id, {"records_count": len(result["records"])})
    except Exception as e:
        set_failed(job_id, str(e))

@router.get("")
def get_institutions():
    return list_institutions(DB_PATH)

@router.post("", status_code=201)
def create_institution(body: InstitutionIn, background_tasks: BackgroundTasks):
    iid = insert_institution(DB_PATH, **body.model_dump())
    job_id = create_job()
    background_tasks.add_task(_scrape, job_id, iid, body.name)
    return {**get_institution(DB_PATH, iid), "scrape_job_id": job_id}

@router.get("/{institution_id}")
def read_institution(institution_id: int):
    inst = get_institution(DB_PATH, institution_id)
    if not inst:
        raise HTTPException(404, "Institution not found")
    return inst

@router.put("/{institution_id}")
def update_institution_endpoint(institution_id: int, body: InstitutionUpdate):
    if not get_institution(DB_PATH, institution_id):
        raise HTTPException(404, "Institution not found")
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if updates:
        update_institution(DB_PATH, institution_id, **updates)
    return get_institution(DB_PATH, institution_id)

@router.delete("/{institution_id}", status_code=204)
def remove_institution(institution_id: int):
    if not get_institution(DB_PATH, institution_id):
        raise HTTPException(404, "Institution not found")
    delete_institution(DB_PATH, institution_id)

@router.post("/{institution_id}/scrape", status_code=202)
def rescrape(institution_id: int, background_tasks: BackgroundTasks):
    inst = get_institution(DB_PATH, institution_id)
    if not inst:
        raise HTTPException(404, "Institution not found")
    job_id = create_job()
    background_tasks.add_task(_scrape, job_id, institution_id, inst["name"])
    return {"job_id": job_id}

@router.get("/{institution_id}/records")
def get_records(institution_id: int):
    if not get_institution(DB_PATH, institution_id):
        raise HTTPException(404, "Institution not found")
    return list_investment_records(DB_PATH, institution_id)

@router.post("/import", status_code=201)
async def import_excel(file: UploadFile = File(...)):
    df = pd.read_excel(io.BytesIO(await file.read()))
    created = 0
    for _, row in df.iterrows():
        name = str(row.get("机构名称", "") or row.get("name", "")).strip()
        if not name:
            continue
        insert_institution(DB_PATH, name=name,
            location=str(row.get("总部地点", "") or ""),
            known_preferences=str(row.get("已知偏好", "") or ""),
            contact_name=str(row.get("联系人", "") or ""),
            contact_wechat=str(row.get("联系方式", "") or ""),
            fa_fee_note="", response_style="", track_updates=1)
        created += 1
    return {"created": created}

def _scrape_all(job_id: str):
    set_running(job_id)
    try:
        insts = [i for i in list_institutions(DB_PATH) if i.get("track_updates")]
        for inst in insts:
            result = scrape_institution_investments(inst["name"], BROWSER_STATE)
            inst_info = {k: v for k, v in result["institution"].items() if v}
            if inst_info:
                update_institution(DB_PATH, inst["id"], **inst_info)
            for r in result["records"]:
                insert_investment_record(DB_PATH, institution_id=inst["id"], **r)
        set_done(job_id, {"count": len(insts)})
    except Exception as e:
        set_failed(job_id, str(e))

@router.post("/scrape-all", status_code=202)
def scrape_all(background_tasks: BackgroundTasks):
    job_id = create_job()
    background_tasks.add_task(_scrape_all, job_id)
    return {"job_id": job_id}

def _fill_descs(job_id: str, institution_id: int):
    set_running(job_id)
    try:
        missing = list_records_missing_desc(DB_PATH, institution_id)
        for rec in missing:
            if rec.get("event_url"):
                desc = scrape_event_description(rec["event_url"])
                if desc:
                    update_investment_record_desc(DB_PATH, rec["id"], desc)
        set_done(job_id, {"filled": len(missing)})
    except Exception as e:
        set_failed(job_id, str(e))

@router.post("/{institution_id}/fill-descs", status_code=202)
def fill_descs(institution_id: int, background_tasks: BackgroundTasks):
    inst = get_institution(DB_PATH, institution_id)
    if not inst:
        raise HTTPException(404, "Institution not found")
    job_id = create_job()
    background_tasks.add_task(_fill_descs, job_id, institution_id)
    return {"job_id": job_id}
