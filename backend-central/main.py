import os
import requests
from fastapi import FastAPI, HTTPException

COUNTRY_BACKEND_URL = os.getenv(
    "COUNTRY_BACKEND_URL",
    "http://backend-country:8000"
)

app = FastAPI(
    title="FutureKawa Backend Central",
    description="Backend siège pour consolider les données des pays.",
    version="0.1.0"
)


def call_country_api(endpoint: str):
    try:
        response = requests.get(
            f"{COUNTRY_BACKEND_URL}/{endpoint}",
            timeout=5
        )
        response.raise_for_status()
        return response.json()

    except requests.RequestException as e:
        raise HTTPException(
            status_code=503,
            detail=f"Impossible de contacter le backend pays : {str(e)}"
        )


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
            {"code": "BR", "name": "Brésil", "enabled": False},
            {"code": "EC", "name": "Équateur", "enabled": True},
            {"code": "CO", "name": "Colombie", "enabled": False}
        ]
    }


@app.get("/lots")
def get_lots(country: str = "equateur"):
    return {
        "country": country,
        "lots": call_country_api("lots")
    }


@app.get("/lots/{lot_id}")
def get_lot_detail(lot_id: int):
    return {
        "lot": call_country_api(f"lots/{lot_id}")
    }


@app.get("/lots/{lot_id}/measurements")
def get_lot_measurements(lot_id: int):
    return {
        "lot_id": lot_id,
        "measurements": call_country_api(f"lots/{lot_id}/measurements")
    }


@app.get("/stocks")
def get_all_stocks():
    return {
        "country": "equateur",
        "stocks": call_country_api("lots")
    }


@app.get("/measurements")
def get_all_measurements():
    return {
        "country": "equateur",
        "measurements": call_country_api("measurements")
    }


@app.get("/alerts")
def get_alerts(country: str = "equateur"):
    return {
        "country": country,
        "alerts": call_country_api("alerts")
    }


@app.get("/dashboard")
def dashboard():
    lots = call_country_api("lots")
    measurements = call_country_api("measurements")
    alerts = call_country_api("alerts")

    return {
        "country": "equateur",
        "statistics": {
            "total_lots": len(lots),
            "total_measurements": len(measurements),
            "total_alerts": len(alerts),
            "healthy_lots": len(
                [lot for lot in lots if lot["status"] == "conforme"]
            ),
            "alert_lots": len(
                [lot for lot in lots if lot["status"] == "en alerte"]
            ),
        },
        "lots": lots,
        "recent_measurements": measurements[:10],
        "recent_alerts": alerts[:5]
    }