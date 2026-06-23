from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.database import get_db
from app.models import Lot, Measurement
from app.schemas import LotCreate, LotResponse, MeasurementCreate, MeasurementResponse

router = APIRouter()

COUNTRY_THRESHOLDS = {
    "Brésil": {"temperature": 29, "humidity": 55},
    "Équateur": {"temperature": 31, "humidity": 60},
    "Colombie": {"temperature": 26, "humidity": 80},
}

TEMP_TOLERANCE = 3
HUMIDITY_TOLERANCE = 2


def evaluate_lot_status(lot: Lot, measurement: Measurement | None = None) -> str:
    if lot.storage_date < datetime.utcnow() - timedelta(days=365):
        return "périmé"

    if measurement:
        thresholds = COUNTRY_THRESHOLDS.get(lot.country)

        if thresholds:
            temp_ok = abs(measurement.temperature - thresholds["temperature"]) <= TEMP_TOLERANCE
            humidity_ok = abs(measurement.humidity - thresholds["humidity"]) <= HUMIDITY_TOLERANCE

            if not temp_ok or not humidity_ok:
                return "en alerte"

    return "conforme"


@router.get("/health")
def health():
    return {"status": "healthy", "service": "backend-country"}


@router.post("/lots", response_model=LotResponse)
def create_lot(lot: LotCreate, db: Session = Depends(get_db)):
    db_lot = Lot(**lot.model_dump())
    db_lot.status = evaluate_lot_status(db_lot)

    db.add(db_lot)
    db.commit()
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

    data = measurement.model_dump()

    if data["timestamp"] is None:
        data["timestamp"] = datetime.utcnow()

    db_measurement = Measurement(**data)

    db.add(db_measurement)

    lot.status = evaluate_lot_status(lot, db_measurement)

    db.commit()
    db.refresh(db_measurement)

    return db_measurement


@router.get("/lots/{lot_id}/measurements", response_model=list[MeasurementResponse])
def get_lot_measurements(lot_id: int, db: Session = Depends(get_db)):
    lot = db.query(Lot).filter(Lot.id == lot_id).first()

    if not lot:
        raise HTTPException(status_code=404, detail="Lot introuvable")

    return db.query(Measurement).filter(
        Measurement.lot_id == lot_id
    ).order_by(Measurement.timestamp.asc()).all()


@router.get("/measurements")
def get_measurements(db: Session = Depends(get_db)):
    return db.query(Measurement)\
             .order_by(Measurement.timestamp.desc())\
             .all()