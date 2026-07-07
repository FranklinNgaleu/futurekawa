import os

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from app.database import engine
from app.models import Base
from app.routes import router
from app.mqtt_subscriber import start_mqtt_subscriber
from app.seed import seed_database
from app.scheduler import check_expired_lots

EXPIRED_LOTS_CHECK_INTERVAL_MINUTES = int(
    os.getenv("EXPIRED_LOTS_CHECK_INTERVAL_MINUTES", "60")
)

Base.metadata.create_all(bind=engine)
seed_database()
check_expired_lots()

app = FastAPI(
    title="FutureKawa Backend Country",
    description="API locale pays pour la gestion des lots, mesures IoT et alertes.",
    version="0.1.0"
)

app.include_router(router)

scheduler = BackgroundScheduler()


@app.on_event("startup")
def startup_event():
    start_mqtt_subscriber()

    scheduler.add_job(
        check_expired_lots,
        "interval",
        minutes=EXPIRED_LOTS_CHECK_INTERVAL_MINUTES,
        id="check_expired_lots",
    )
    scheduler.start()


@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown(wait=False)


@app.get("/")
def root():
    return {"message": "Backend Country OK"}