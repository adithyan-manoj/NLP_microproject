from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["service"] == "CricInsight"
    assert data["database"] == "Ready"
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
        "prompt": "How has Virat Kohli performed against Australia in ODIs?"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "Virat Kohli" in data["scope"]["players"]
    assert data["scope"]["opponent"] == "Australia"
    assert data["scope"]["format"] == "ODI"
    assert data["stats"]["total_runs"] > 1000
    assert data["stats"]["batting_average"] > 40
    assert len(data["chart"]["series"]) == 1
    assert len(data["chart"]["series"][0]["data"]) > 0
    assert "Virat Kohli" in data["insight"]

def test_analyze_player_comparison():
    response = client.post("/api/analyze", json={
        "prompt": "Compare Rohit Sharma and Virat Kohli in T20 internationals"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["scope"]["players"]) == 2
    assert "Rohit Sharma" in data["scope"]["players"]
    assert "Virat Kohli" in data["scope"]["players"]
    assert len(data["chart"]["series"]) == 2
    assert data["chart"]["chart_type"] == "bar"
    assert "Rohit Sharma" in data["insight"]
    assert "Virat Kohli" in data["insight"]
