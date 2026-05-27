from fastapi import FastAPI

app = FastAPI(
    title="FutureKawa Backend Central",
    description="Backend central du siège pour consolider les données des pays.",
    version="0.1.0"
)

@app.get("/")
def root():
    return {"message": "Backend Central OK"}

@app.get("/health")
def health_check():
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