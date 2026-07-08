from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.database import get_db
from app.email_service import send_grouped_alert_email
from app.models import Lot, Measurement
from app.mqtt_subscriber import apply_measurement
from app.schemas import AlertResponse, LotCreate, LotResponse, MeasurementCreate, MeasurementResponse
from app.models import Lot, Measurement, Alert
from app.thresholds import get_country_thresholds, get_own_country, TEMP_TOLERANCE, HUMIDITY_TOLERANCE

router = APIRouter()

DEFAULT_PAGE_LIMIT = 100
MAX_PAGE_LIMIT = 500


def evaluate_lot_status(lot: Lot, measurement: Measurement | None = None) -> str:
    if lot.storage_date < datetime.utcnow() - timedelta(days=365):
        return "périmé"

    if measurement:
        thresholds = get_country_thresholds(lot.country)

        if thresholds:
            temp_ok = abs(measurement.temperature - thresholds["temperature"]) <= TEMP_TOLERANCE
            humidity_ok = abs(measurement.humidity - thresholds["humidity"]) <= HUMIDITY_TOLERANCE

            if not temp_ok or not humidity_ok:
                return "en alerte"

    return "conforme"


@router.get("/health")
def health():
    return {"status": "healthy", "service": "backend-country"}


@router.post("/lots", response_model=LotResponse, status_code=201)
def create_lot(lot: LotCreate, db: Session = Depends(get_db)):
    data = lot.model_dump()
    data["country"] = get_own_country()

    db_lot = Lot(**data)
    db_lot.status = evaluate_lot_status(db_lot)

    db.add(db_lot)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Un lot avec le code '{lot.lot_code}' existe déjà."
        )

    db.refresh(db_lot)

    return db_lot


@router.get("/lots", response_model=list[LotResponse])
def get_lots(db: Session = Depends(get_db)):
    return db.query(Lot).order_by(Lot.storage_date.asc()).all()


@router.get("/lots/{lot_id}", response_model=LotResponse)
def get_lot(lot_id: int, db: Session = Depends(get_db)):
    lot = db.query(Lot).filter(Lot.id == lot_id).first()

    if not lot:
        raise HTTPException(status_code=404, detail="Lot introuvable")

    return lot


@router.post("/measurements", response_model=MeasurementResponse)
def create_measurement(measurement: MeasurementCreate, db: Session = Depends(get_db)):
    lot = db.query(Lot).filter(Lot.id == measurement.lot_id).first()

    if not lot:
        raise HTTPException(status_code=404, detail="Lot introuvable")

    timestamp = measurement.timestamp or datetime.utcnow()

    generated_alerts, measurements, _ = apply_measurement(
        db,
        country=lot.country,
        warehouse=lot.warehouse,
        temperature=measurement.temperature,
        humidity=measurement.humidity,
        timestamp=timestamp,
        source="iot",
    )

    db.commit()

    db_measurement = next(m for m in measurements if m.lot_id == lot.id)
    db.refresh(db_measurement)

    if generated_alerts:
        send_grouped_alert_email(generated_alerts)

    return db_measurement


@router.get("/lots/{lot_id}/measurements", response_model=list[MeasurementResponse])
def get_lot_measurements(
    lot_id: int,
    limit: int = Query(DEFAULT_PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    lot = db.query(Lot).filter(Lot.id == lot_id).first()

    if not lot:
        raise HTTPException(status_code=404, detail="Lot introuvable")

    return (
        db.query(Measurement)
        .filter(Measurement.lot_id == lot_id)
        .order_by(Measurement.timestamp.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/measurements")
def get_measurements(
    limit: int = Query(DEFAULT_PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return (
        db.query(Measurement)
        .order_by(Measurement.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

@router.get("/alerts", response_model=list[AlertResponse])
def get_alerts(db: Session = Depends(get_db)):
    return db.query(Alert).order_by(Alert.timestamp.desc()).all()