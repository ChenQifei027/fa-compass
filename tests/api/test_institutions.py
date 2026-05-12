import os, tempfile
_db = tempfile.mktemp(suffix=".db")
os.environ["DB_PATH"] = _db

from fastapi.testclient import TestClient
from api.main import app
from core.database import init_db
init_db(_db)

client = TestClient(app)

def test_list_returns_list():
    r = client.get("/api/institutions")
    assert r.status_code == 200

def test_create_and_read():
    r = client.post("/api/institutions", json={"name": "红杉中国"})
    assert r.status_code == 201
    iid = r.json()["id"]
    assert "scrape_job_id" in r.json()
    assert client.get(f"/api/institutions/{iid}").json()["name"] == "红杉中国"

def test_update():
    r = client.post("/api/institutions", json={"name": "高瓴"})
    iid = r.json()["id"]
    client.put(f"/api/institutions/{iid}", json={"location": "北京"})
    assert client.get(f"/api/institutions/{iid}").json()["location"] == "北京"

def test_delete():
    r = client.post("/api/institutions", json={"name": "ToDelete"})
    iid = r.json()["id"]
    client.delete(f"/api/institutions/{iid}")
    assert client.get(f"/api/institutions/{iid}").status_code == 404

def test_records_empty():
    r = client.post("/api/institutions", json={"name": "NoRecords"})
    iid = r.json()["id"]
    assert client.get(f"/api/institutions/{iid}/records").json() == []
