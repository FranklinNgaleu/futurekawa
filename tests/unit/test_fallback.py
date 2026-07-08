from datetime import datetime, timedelta

import pytest

from app.database import Base, SessionLocal, engine
from app.fallback import apply_fallback_measurements, is_stale, jittered
from app.models import FallbackReading, Lot, Measurement


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    yield session

    session.rollback()
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()
    session.close()


def test_is_stale_when_no_previous_measurement():
    assert is_stale(None, datetime.utcnow(), 15) is True


def test_is_stale_when_last_measurement_too_old():
    now = datetime.utcnow()
    last = now - timedelta(minutes=30)
    assert is_stale(last, now, 15) is True


def test_is_stale_when_recent_measurement_exists():
    now = datetime.utcnow()
    last = now - timedelta(minutes=2)
    assert is_stale(last, now, 15) is False


def test_jittered_stays_within_expected_bounds():
    for _ in range(50):
        value = jittered(31.0, 0.5)
        assert 30.5 <= value <= 31.5


def test_apply_fallback_creates_measurement_when_no_prior_data(db_session):
    lot = Lot(
        lot_code="LOT-FALLBACK-001",
        country="equateur",
        farm="Ferme Test",
        warehouse="WH-EQ-01",
        storage_date=datetime.utcnow() - timedelta(days=10),
        status="conforme",
    )
    db_session.add(lot)
    db_session.add(FallbackReading(
        country="equateur",
        warehouse="WH-EQ-01",
        temperature=31.0,
        humidity=60.0,
    ))
    db_session.commit()

    apply_fallback_measurements()

    measurements = db_session.query(Measurement).filter(Measurement.lot_id == lot.id).all()
    assert len(measurements) == 1
    assert measurements[0].source == "fallback"


def test_apply_fallback_skips_when_recent_measurement_exists(db_session):
    lot = Lot(
        lot_code="LOT-FALLBACK-002",
        country="equateur",
        farm="Ferme Test",
        warehouse="WH-EQ-02",
        storage_date=datetime.utcnow() - timedelta(days=10),
        status="conforme",
    )
    db_session.add(lot)
    db_session.add(FallbackReading(
        country="equateur",
        warehouse="WH-EQ-02",
        temperature=31.0,
        humidity=60.0,
    ))
    db_session.commit()

    db_session.add(Measurement(
        lot_id=lot.id,
        country="equateur",
        warehouse="WH-EQ-02",
        temperature=31.0,
        humidity=60.0,
        status="OK",
        source="iot",
        timestamp=datetime.utcnow(),
    ))
    db_session.commit()

    apply_fallback_measurements()

    measurements = db_session.query(Measurement).filter(Measurement.lot_id == lot.id).all()
    assert len(measurements) == 1
    assert measurements[0].source == "iot"


def test_apply_fallback_does_not_override_perime_status(db_session):
    lot = Lot(
        lot_code="LOT-FALLBACK-003",
        country="equateur",
        farm="Ferme Test",
        warehouse="WH-EQ-01",
        storage_date=datetime.utcnow() - timedelta(days=400),
        status="périmé",
    )
    db_session.add(lot)
    db_session.add(FallbackReading(
        country="equateur",
        warehouse="WH-EQ-01",
        temperature=31.0,
        humidity=60.0,
    ))
    db_session.commit()

    apply_fallback_measurements()

    db_session.refresh(lot)
    assert lot.status == "périmé"
