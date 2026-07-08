import os
import uuid
from datetime import datetime, timedelta

import requests

BASE_URL = os.getenv("BACKEND_COUNTRY_URL", "http://localhost:8001")


def unique_lot_code():
    return f"LOT-TEST-{uuid.uuid4().hex[:12]}"


def make_lot_payload(**overrides):
    payload = {
        "lot_code": unique_lot_code(),
        "country": "equateur",
        "farm": "Ferme de test",
        "warehouse": "WH-EQ-01",
        "storage_date": datetime.utcnow().isoformat(),
    }
    payload.update(overrides)
    return payload


def create_lot(**overrides):
    payload = make_lot_payload(**overrides)
    response = requests.post(f"{BASE_URL}/lots", json=payload, timeout=5)
    return response, payload


def test_create_lot_sets_initial_status():
    response, payload = create_lot()

    assert response.status_code == 201
    data = response.json()
    assert data["lot_code"] == payload["lot_code"]
    assert data["status"] == "conforme"
    assert "id" in data


def test_create_lot_duplicate_code_returns_409():
    _, payload = create_lot()

    response = requests.post(f"{BASE_URL}/lots", json=payload, timeout=5)

    assert response.status_code == 409
    assert "detail" in response.json()


def test_get_lot_not_found_returns_404():
    response = requests.get(f"{BASE_URL}/lots/999999999", timeout=5)
    assert response.status_code == 404


def test_create_measurement_recalculates_status():
    response, _ = create_lot()
    lot_id = response.json()["id"]

    measurement_payload = {"lot_id": lot_id, "temperature": 45.0, "humidity": 60.0}
    meas_response = requests.post(f"{BASE_URL}/measurements", json=measurement_payload, timeout=5)
    assert meas_response.status_code == 200

    lot_response = requests.get(f"{BASE_URL}/lots/{lot_id}", timeout=5)
    assert lot_response.json()["status"] == "en alerte"


def test_create_measurement_unknown_lot_returns_404():
    measurement_payload = {"lot_id": 999999999, "temperature": 30.0, "humidity": 60.0}
    response = requests.post(f"{BASE_URL}/measurements", json=measurement_payload, timeout=5)
    assert response.status_code == 404


def test_lot_measurements_sorted_chronologically():
    response, _ = create_lot()
    lot_id = response.json()["id"]

    base = datetime.utcnow()
    for offset_minutes in [2, 0, 1]:
        timestamp = (base + timedelta(minutes=offset_minutes)).isoformat()
        requests.post(
            f"{BASE_URL}/measurements",
            json={
                "lot_id": lot_id,
                "temperature": 31.0,
                "humidity": 60.0,
                "timestamp": timestamp,
            },
            timeout=5,
        )

    meas_response = requests.get(f"{BASE_URL}/lots/{lot_id}/measurements", timeout=5)
    measurements = meas_response.json()

    timestamps = [m["timestamp"] for m in measurements]
    assert timestamps == sorted(timestamps)


def test_lot_measurements_pagination():
    response, _ = create_lot(warehouse=f"WH-PAGINATION-{uuid.uuid4().hex[:6]}")
    lot_id = response.json()["id"]

    base = datetime.utcnow()
    for i in range(5):
        requests.post(
            f"{BASE_URL}/measurements",
            json={
                "lot_id": lot_id,
                "temperature": 31.0,
                "humidity": 60.0,
                "timestamp": (base + timedelta(minutes=i)).isoformat(),
            },
            timeout=5,
        )

    first_page = requests.get(
        f"{BASE_URL}/lots/{lot_id}/measurements", params={"limit": 2, "offset": 0}, timeout=5
    ).json()
    second_page = requests.get(
        f"{BASE_URL}/lots/{lot_id}/measurements", params={"limit": 2, "offset": 2}, timeout=5
    ).json()

    assert len(first_page) == 2
    assert len(second_page) == 2
    assert {m["id"] for m in first_page}.isdisjoint({m["id"] for m in second_page})


def test_measurements_pagination_limit_is_capped():
    response = requests.get(f"{BASE_URL}/measurements", params={"limit": 10000}, timeout=5)
    assert response.status_code == 422


def test_lots_sorted_by_storage_date_ascending_fifo():
    now = datetime.utcnow()
    create_lot(storage_date=(now - timedelta(days=100)).isoformat())
    create_lot(storage_date=(now - timedelta(days=1)).isoformat())

    response = requests.get(f"{BASE_URL}/lots", timeout=5)
    lots = response.json()

    dates = [datetime.fromisoformat(lot["storage_date"]) for lot in lots]
    assert dates == sorted(dates)
