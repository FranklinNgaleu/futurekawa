import os
import uuid
from datetime import datetime

import pytest
import requests

COUNTRY_PORTS = {
    "equateur": os.getenv("BACKEND_COUNTRY_EQUATEUR_URL", "http://localhost:8001"),
    "bresil": os.getenv("BACKEND_COUNTRY_BRESIL_URL", "http://localhost:8002"),
    "colombie": os.getenv("BACKEND_COUNTRY_COLOMBIE_URL", "http://localhost:8003"),
}

COUNTRY_CODE_PREFIXES = {
    "equateur": "LOT-EQ-",
    "bresil": "LOT-BR-",
    "colombie": "LOT-CO-",
}


@pytest.mark.parametrize("country", ["equateur", "bresil", "colombie"])
def test_each_country_backend_is_healthy(country):
    response = requests.get(f"{COUNTRY_PORTS[country]}/health", timeout=5)
    assert response.status_code == 200


@pytest.mark.parametrize("country", ["equateur", "bresil", "colombie"])
def test_each_country_backend_has_seeded_lots_for_its_own_country(country):
    response = requests.get(f"{COUNTRY_PORTS[country]}/lots", timeout=5)
    assert response.status_code == 200

    lots = response.json()
    assert len(lots) >= 6

    # tous les lots renvoyés par cette instance appartiennent bien à son propre pays,
    # quel que soit le code lot (d'autres tests peuvent créer des lots hors seed)
    for lot in lots:
        assert lot["country"] == country

    prefix = COUNTRY_CODE_PREFIXES[country]
    seeded_codes = {lot["lot_code"] for lot in lots if lot["lot_code"].startswith(prefix)}
    assert len(seeded_codes) >= 6


@pytest.mark.parametrize(
    "own_country,spoofed_country",
    [
        ("equateur", "colombie"),
        ("bresil", "equateur"),
        ("colombie", "bresil"),
    ],
)
def test_country_field_is_ignored_and_forced_server_side(own_country, spoofed_country):
    payload = {
        "lot_code": f"LOT-SPOOF-{uuid.uuid4().hex[:10]}",
        "country": spoofed_country,
        "farm": "Ferme Test",
        "warehouse": "WH-TEST-01",
        "storage_date": datetime.utcnow().isoformat(),
    }

    response = requests.post(f"{COUNTRY_PORTS[own_country]}/lots", json=payload, timeout=5)
    assert response.status_code == 201
    assert response.json()["country"] == own_country

    lot_id = response.json()["id"]
    stored = requests.get(f"{COUNTRY_PORTS[own_country]}/lots/{lot_id}", timeout=5)
    assert stored.json()["country"] == own_country


def test_countries_do_not_share_data():
    lots_by_country = {
        country: {lot["lot_code"] for lot in requests.get(f"{url}/lots", timeout=5).json()}
        for country, url in COUNTRY_PORTS.items()
    }

    assert lots_by_country["equateur"].isdisjoint(lots_by_country["bresil"])
    assert lots_by_country["equateur"].isdisjoint(lots_by_country["colombie"])
    assert lots_by_country["bresil"].isdisjoint(lots_by_country["colombie"])
