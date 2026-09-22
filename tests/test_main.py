from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

def test_liveness_probe():
    """Verify the liveness probe returns 200 OK."""
    response = client.get("/healthz/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}

def test_metrics_endpoint():
    """Verify the Prometheus metrics endpoint is exposed."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "python_gc_objects_collected_total" in response.text

def test_city_not_found(monkeypatch):
    """Verify proper 404 handling when a city does not exist."""
    # Mock get_coordinates to simulate city not found
    from fastapi import HTTPException
    def mock_get_coords(city):
        raise HTTPException(status_code=404, detail=f"City '{city}' not found")

    monkeypatch.setattr("main.get_coordinates", mock_get_coords)
    response = client.get("/aqi?city=NonExistentCityXYZ")
    assert response.status_code == 404
