"""
Integration Tests for Phase 3: Backend API Endpoints.
Verifies Phase 3 Exit Conditions:
- A structured test query produces real database-derived results
- /api/chat/query returns validated ChatQueryResponse with fl_chart ready chart JSON
- /api/health reports online status and counts
- /api/dataset/coverage and /api/dataset/status respond with accurate data
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.ingestion.ingestion_service import ingest_file

client = TestClient(app)

@pytest.fixture(autouse=True)
def ensure_dataset():
    fixture_path = settings.FIXTURES_DIR / "test_odi_1.json"
    ingest_file(fixture_path)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["counts"]["matches"] >= 1
    assert data["counts"]["deliveries"] >= 14

def test_dataset_endpoints():
    res_status = client.get("/api/dataset/status")
    assert res_status.status_code == 200
    assert res_status.json()["status"] == "ready"

    res_cov = client.get("/api/dataset/coverage")
    assert res_cov.status_code == 200
    cov_data = res_cov.json()
    assert cov_data["total_matches"] >= 1
    assert len(cov_data["teams"]) >= 2

def test_chat_query_single_player():
    req_payload = {
        "prompt": "Show Rohit Sharma stats"
    }
    response = client.post("/api/chat/query", json=req_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "request_id" in data
    assert len(data["metrics"]) > 0
    assert "Rohit Sharma" in data["answer"] and ("scored" in data["answer"] or "runs" in data["answer"])

def test_chat_query_comparison():
    req_payload = {
        "prompt": "Compare Rohit Sharma and Virat Kohli in ODIs"
    }
    response = client.post("/api/chat/query", json=req_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["metrics"]) == 2
    assert data["chart"]["chart_type"] == "grouped_bar"
    assert "Comparison" in data["chart"]["title"]

def test_chat_query_clarification():
    req_payload = {
        "prompt": "How did he play?"  # Ambiguous pronoun with no context
    }
    response = client.post("/api/chat/query", json=req_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "clarification_required"
    assert data["clarification_required"] is True
    assert len(data["clarification_options"]) > 0

def test_catalog_metadata_endpoints():
    res_teams = client.get("/api/teams")
    assert res_teams.status_code == 200
    teams = res_teams.json()
    assert isinstance(teams, list)
    assert len(teams) >= 2

    res_comp = client.get("/api/competitions")
    assert res_comp.status_code == 200
    comps = res_comp.json()
    assert isinstance(comps, list)

    res_venues = client.get("/api/venues")
    assert res_venues.status_code == 200
    venues = res_venues.json()
    assert isinstance(venues, list)
    assert len(venues) >= 1

def test_ingestion_and_evaluation_endpoints():
    res_hist = client.get("/api/ingestion/history")
    assert res_hist.status_code == 200
    assert isinstance(res_hist.json(), list)

    res_queries = client.get("/api/evaluation/queries")
    assert res_queries.status_code == 200
    assert isinstance(res_queries.json(), list)
    assert len(res_queries.json()) > 0  # logged queries from previous tests

    res_import = client.post("/api/ingestion/import")
    assert res_import.status_code == 200
    assert res_import.json()["files_processed"] >= 1
