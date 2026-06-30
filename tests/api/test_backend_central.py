import requests

BASE_URL = "http://localhost:8000"


def test_health():
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_countries():
    response = requests.get(f"{BASE_URL}/countries")
    assert response.status_code == 200
    assert "countries" in response.json()


def test_dashboard():
    response = requests.get(f"{BASE_URL}/dashboard")
    assert response.status_code == 200
    assert "statistics" in response.json()


def test_alerts():
    response = requests.get(f"{BASE_URL}/alerts")
    assert response.status_code == 200
    assert "alerts" in response.json()