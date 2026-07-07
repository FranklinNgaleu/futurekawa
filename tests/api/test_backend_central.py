import os

import requests

BASE_URL = os.getenv("BACKEND_CENTRAL_URL", "http://localhost:8000")


def test_health():
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_countries_lists_equateur_enabled():
    response = requests.get(f"{BASE_URL}/countries", timeout=5)
    assert response.status_code == 200

    countries = response.json()["countries"]
    equateur = next(c for c in countries if c["id"] == "equateur")
    assert equateur["enabled"] is True


def test_unknown_country_returns_404():
    response = requests.get(f"{BASE_URL}/lots", params={"country": "narnia"}, timeout=5)
    assert response.status_code == 404


def test_unknown_country_dashboard_returns_404():
    response = requests.get(f"{BASE_URL}/dashboard", params={"country": "narnia"}, timeout=5)
    assert response.status_code == 404


def test_dashboard_global_returns_200_with_per_country_key():
    response = requests.get(f"{BASE_URL}/dashboard/global", timeout=10)
    assert response.status_code == 200

    data = response.json()
    assert "statistics" in data
    assert "countries" in data
    assert "equateur" in data["countries"]
    assert data["countries"]["equateur"]["status"] in ("ok", "unreachable")
