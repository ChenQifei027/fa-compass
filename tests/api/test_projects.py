import os, tempfile
_db = tempfile.mktemp(suffix=".db")
os.environ["DB_PATH"] = _db

from fastapi.testclient import TestClient
from api.main import app
from core.database import init_db
init_db(_db)

client = TestClient(app)

def test_list_returns_list():
    r = client.get("/api/projects")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

def test_create_and_read():
    r = client.post("/api/projects", json={"name": "TestCo", "sector": "AI"})
    assert r.status_code == 201
    pid = r.json()["id"]
    r2 = client.get(f"/api/projects/{pid}")
    assert r2.json()["name"] == "TestCo"
    assert r2.json()["sector"] == "AI"

def test_update():
    r = client.post("/api/projects", json={"name": "UpdateCo"})
    pid = r.json()["id"]
    client.put(f"/api/projects/{pid}", json={"sector": "Hardware"})
    assert client.get(f"/api/projects/{pid}").json()["sector"] == "Hardware"

def test_delete():
    r = client.post("/api/projects", json={"name": "DeleteCo"})
    pid = r.json()["id"]
    client.delete(f"/api/projects/{pid}")
    assert client.get(f"/api/projects/{pid}").status_code == 404

def test_read_not_found():
    assert client.get("/api/projects/99999").status_code == 404

def test_funding_rounds_empty():
    r = client.post("/api/projects", json={"name": "FundCo"})
    pid = r.json()["id"]
    r2 = client.get(f"/api/projects/{pid}/funding-rounds")
    assert r2.status_code == 200
    assert r2.json() == []
