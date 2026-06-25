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
            {"code": "BR", "name": "Brésil"},
            {"code": "EC", "name": "Équateur"},
            {"code": "CO", "name": "Colombie"}
        ]
    }

@app.get("/stocks")
def get_all_stocks():
    try:
        response = requests.get(f"{COUNTRY_BACKEND_URL}/lots", timeout=5)
        response.raise_for_status()
        return {
            "source": "backend-country",
            "data": response.json()
        }
    except requests.RequestException as e:
        raise HTTPException(
            status_code=503,
            detail=f"Impossible de récupérer les stocks pays : {str(e)}"
        )

@app.get("/measurements")
def get_all_measurements():
    try:
        response = requests.get(f"{COUNTRY_BACKEND_URL}/measurements", timeout=5)
        response.raise_for_status()
        return {
            "source": "backend-country",
            "data": response.json()
        }
    except requests.RequestException as e:
        raise HTTPException(
            status_code=503,
            detail=f"Impossible de récupérer les mesures pays : {str(e)}"
        )