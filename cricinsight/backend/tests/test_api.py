import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.ingestion.ingestion_service import ingest_file

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_fixture():
    fixture_path = settings.FIXTURES_DIR / "test_odi_1.json"
    ingest_file(fixture_path, force=True)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["service"] == "CricInsight"
    assert data["database_ready"] is True
    assert data["counts"]["matches"] > 0
    assert data["counts"]["deliveries"] > 0
    assert data["counts"]["players"] > 0

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "CricInsight" in data["message"]

def test_analyze_single_player():
    response = client.post("/api/analyze", json={
        "prompt": "Show Rohit Sharma stats in ODIs"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "Rohit Sharma" in data["scope"]["players"]
    assert data["stats"]["total_runs"] > 0
    assert "Rohit Sharma" in data["insight"]

def test_analyze_player_comparison():
    response = client.post("/api/analyze", json={
        "prompt": "Compare Rohit Sharma and Virat Kohli in ODIs"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["scope"]["players"]) == 2
    assert "Rohit Sharma" in data["scope"]["players"]
    assert "Virat Kohli" in data["scope"]["players"]
    assert data["chart"]["chart_type"] == "grouped_bar"
    assert "Rohit Sharma" in data["insight"] or "Rohit Sharma" in data["answer"]
