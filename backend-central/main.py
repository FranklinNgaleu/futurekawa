import json
import os

import requests
from fastapi import Body, FastAPI, HTTPException

DEFAULT_COUNTRY = "equateur"
MAX_PAGE_LIMIT = 500

COUNTRY_DISPLAY_NAMES = {
    "bresil": "Brésil",
    "equateur": "Équateur",
    "colombie": "Colombie",
}


def load_country_backends():
    raw = os.getenv("COUNTRY_BACKENDS")

    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict) and parsed:
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass

    if os.getenv("COUNTRY_BACKEND_URL"):
        return {DEFAULT_COUNTRY: os.getenv("COUNTRY_BACKEND_URL")}

    return {
        "equateur": "http://backend-country-equateur:8000",
        "bresil": "http://backend-country-bresil:8000",
        "colombie": "http://backend-country-colombie:8000",
    }


COUNTRY_BACKENDS = load_country_backends()

app = FastAPI(
    title="FutureKawa Backend Central",
    description="Backend siège pour consolider les données des pays.",
    version="0.1.0"
)


def get_backend_url(country: str) -> str:
    url = COUNTRY_BACKENDS.get(country.lower())

    if not url:
        raise HTTPException(
            status_code=404,
            detail=f"Pays inconnu ou non activé : {country}"
        )

    return url


def call_country_api(country: str, endpoint: str, params: dict = None):
    base_url = get_backend_url(country)

    try:
        response = requests.get(f"{base_url}/{endpoint}", params=params, timeout=5)
        response.raise_for_status()
        return response.json()

    except requests.RequestException as e:
        raise HTTPException(
            status_code=503,
            detail=f"Impossible de contacter le backend pays ({country}) : {str(e)}"
        )


def build_statistics(lots: list, measurements: list, alerts: list) -> dict:
    return {
        "total_lots": len(lots),
        "total_measurements": len(measurements),
        "total_alerts": len(alerts),
        "healthy_lots": len([lot for lot in lots if lot.get("status") == "conforme"]),
        "alert_lots": len([lot for lot in lots if lot.get("status") == "en alerte"]),
        "expired_lots": len([lot for lot in lots if lot.get("status") == "périmé"]),
    }


@app.get("/")
def root():
    return {"message": "Backend Central OK"}


@app.get("/health")
def health():
    return {"status": "healthy", "service": "backend-central"}


@app.get("/countries")
def get_countries():
    return {
        "countries": [
            {
                "id": code,
                "name": COUNTRY_DISPLAY_NAMES.get(code, code),
                "enabled": code in COUNTRY_BACKENDS
            }
            for code in COUNTRY_DISPLAY_NAMES
        ]
    }


@app.get("/lots")
def get_lots(country: str = DEFAULT_COUNTRY):
    return {
        "country": country,
        "lots": call_country_api(country, "lots")
    }


def relay_post(country: str, endpoint: str, payload: dict = None):
    base_url = get_backend_url(country)

    try:
        response = requests.post(f"{base_url}/{endpoint}", json=payload, timeout=5)
    except requests.RequestException as e:
        raise HTTPException(
            status_code=503,
            detail=f"Impossible de contacter le backend pays ({country}) : {str(e)}"
        )

    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text

        raise HTTPException(status_code=response.status_code, detail=detail)

    return response.json()


@app.post("/lots", status_code=201)
def create_lot(payload: dict = Body(...), country: str = DEFAULT_COUNTRY):
    return relay_post(country, "lots", payload)


@app.get("/lots/{lot_id}")
def get_lot_detail(lot_id: int, country: str = DEFAULT_COUNTRY):
    return {
        "country": country,
        "lot": call_country_api(country, f"lots/{lot_id}")
    }


@app.post("/lots/{lot_id}/ship")
def ship_lot(lot_id: int, country: str = DEFAULT_COUNTRY):
    return relay_post(country, f"lots/{lot_id}/ship")


@app.get("/lots/{lot_id}/measurements")
def get_lot_measurements(lot_id: int, country: str = DEFAULT_COUNTRY, limit: int = 100, offset: int = 0):
    return {
        "country": country,
        "lot_id": lot_id,
        "measurements": call_country_api(
            country, f"lots/{lot_id}/measurements", params={"limit": limit, "offset": offset}
        )
    }


@app.get("/stocks")
def get_all_stocks(country: str = DEFAULT_COUNTRY):
    return {
        "country": country,
        "stocks": call_country_api(country, "lots")
    }


@app.get("/measurements")
def get_all_measurements(country: str = DEFAULT_COUNTRY, limit: int = 100, offset: int = 0):
    return {
        "country": country,
        "measurements": call_country_api(country, "measurements", params={"limit": limit, "offset": offset})
    }


@app.get("/alerts")
def get_alerts(country: str = DEFAULT_COUNTRY):
    return {
        "country": country,
        "alerts": call_country_api(country, "alerts")
    }


@app.get("/dashboard")
def dashboard(country: str = DEFAULT_COUNTRY):
    lots = call_country_api(country, "lots")
    measurements = call_country_api(country, "measurements", params={"limit": MAX_PAGE_LIMIT})
    alerts = call_country_api(country, "alerts")

    return {
        "country": country,
        "statistics": build_statistics(lots, measurements, alerts),
        "lots": lots,
        "recent_measurements": measurements[:10],
        "recent_alerts": alerts[:5]
    }


@app.get("/dashboard/global")
def dashboard_global():
    countries_data = {}

    totals = {
        "total_lots": 0,
        "total_measurements": 0,
        "total_alerts": 0,
        "healthy_lots": 0,
        "alert_lots": 0,
        "expired_lots": 0,
    }

    for country in COUNTRY_BACKENDS:
        try:
            lots = call_country_api(country, "lots")
            measurements = call_country_api(country, "measurements", params={"limit": MAX_PAGE_LIMIT})
            alerts = call_country_api(country, "alerts")

            stats = build_statistics(lots, measurements, alerts)

            countries_data[country] = {
                "status": "ok",
                "statistics": stats
            }

            for key in totals:
                totals[key] += stats[key]

        except HTTPException as e:
            countries_data[country] = {
                "status": "unreachable",
                "detail": e.detail
            }

    return {
        "statistics": totals,
        "countries": countries_data
    }
