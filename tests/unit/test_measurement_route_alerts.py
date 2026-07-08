from datetime import datetime, timedelta

from app.models import Alert, Lot
from app.routes import create_measurement
from app.schemas import MeasurementCreate


def make_lot(db, warehouse="WH-EQ-01", country="equateur"):
    lot = Lot(
        lot_code=f"LOT-ROUTE-{warehouse}",
        country=country,
        farm="Ferme Test",
        warehouse=warehouse,
        storage_date=datetime.utcnow() - timedelta(days=5),
        status="conforme",
    )
    db.add(lot)
    db.commit()
    db.refresh(lot)
    return lot


def test_measurement_within_range_creates_no_alert_and_sends_no_email(db_session, monkeypatch):
    sent = []
    monkeypatch.setattr("app.routes.send_grouped_alert_email", lambda alerts: sent.append(alerts))

    lot = make_lot(db_session)
    measurement = MeasurementCreate(lot_id=lot.id, temperature=31.0, humidity=60.0)

    create_measurement(measurement, db_session)

    assert sent == []
    assert db_session.query(Alert).count() == 0


def test_out_of_range_measurement_creates_alert_and_triggers_email(db_session, monkeypatch):
    sent = []
    monkeypatch.setattr("app.routes.send_grouped_alert_email", lambda alerts: sent.append(alerts))

    lot = make_lot(db_session)
    measurement = MeasurementCreate(lot_id=lot.id, temperature=45.0, humidity=60.0)

    create_measurement(measurement, db_session)

    alerts = db_session.query(Alert).filter(Alert.warehouse == lot.warehouse).all()
    assert len(alerts) == 1
    assert alerts[0].type == "TEMPERATURE_OUT_OF_RANGE"

    assert len(sent) == 1
    assert sent[0][0]["type"] == "TEMPERATURE_OUT_OF_RANGE"
