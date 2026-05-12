from fastapi.testclient import TestClient
from api.main import app
from api import jobs as job_store

client = TestClient(app)

def test_poll_unknown_job():
    r = client.get("/api/jobs/nonexistent")
    assert r.status_code == 404

def test_poll_pending():
    jid = job_store.create_job()
    r = client.get(f"/api/jobs/{jid}")
    assert r.json()["status"] == "pending"

def test_poll_completed():
    jid = job_store.create_job()
    job_store.set_done(jid, {"n": 3})
    r = client.get(f"/api/jobs/{jid}")
    assert r.json() == {"status": "completed", "result": {"n": 3}, "error": None}
