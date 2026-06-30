import requests

BASE_URL = "http://localhost:8001"


def test_health():
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_get_lots():
    response = requests.get(f"{BASE_URL}/lots")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_measurements():
    response = requests.get(f"{BASE_URL}/measurements")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_alerts():
    response = requests.get(f"{BASE_URL}/alerts")
    assert response.status_code == 200
    assert isinstance(response.json(), list)