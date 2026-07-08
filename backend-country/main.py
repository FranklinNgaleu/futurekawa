import os

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from app.database import engine
from app.models import Base
from app.routes import router
from app.mqtt_subscriber import start_mqtt_subscriber
from app.seed import seed_database, seed_fallback_readings
from app.scheduler import check_expired_lots
from app.fallback import apply_fallback_measurements

EXPIRED_LOTS_CHECK_INTERVAL_MINUTES = int(
    os.getenv("EXPIRED_LOTS_CHECK_INTERVAL_MINUTES", "60")
)
FALLBACK_CHECK_INTERVAL_MINUTES = int(
    os.getenv("FALLBACK_CHECK_INTERVAL_MINUTES", "5")
)

Base.metadata.create_all(bind=engine)
seed_database()
seed_fallback_readings()
check_expired_lots()
apply_fallback_measurements()

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
    scheduler.add_job(
        apply_fallback_measurements,
        "interval",
        minutes=FALLBACK_CHECK_INTERVAL_MINUTES,
        id="apply_fallback_measurements",
    )
    scheduler.start()


@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown(wait=False)


@app.get("/")
def root():
    return {"message": "Backend Country OK"}