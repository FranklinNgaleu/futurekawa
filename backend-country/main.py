from fastapi import FastAPI
from app.database import engine
from app.models import Base
from app.routes import router
from app.mqtt_subscriber import start_mqtt_subscriber


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FutureKawa Backend Country",
    description="API locale pays pour la gestion des lots, mesures IoT et alertes.",
    version="0.1.0"
)

app.include_router(router)

@app.on_event("startup")
def startup_event():
    start_mqtt_subscriber()


@app.get("/")
def root():
    return {"message": "Backend Country OK"}