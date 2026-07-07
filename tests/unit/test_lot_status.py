from datetime import datetime, timedelta

from app.models import Lot, Measurement
from app.routes import evaluate_lot_status


def make_lot(storage_date, country="equateur"):
    return Lot(
        lot_code="LOT-TEST",
        country=country,
        farm="Ferme Test",
        warehouse="WH-EQ-01",
        storage_date=storage_date,
        status="conforme",
    )


def make_measurement(temperature, humidity):
    return Measurement(
        country="equateur",
        warehouse="WH-EQ-01",
        temperature=temperature,
        humidity=humidity,
    )


def test_recent_lot_without_measurement_is_conforme():
    lot = make_lot(datetime.utcnow() - timedelta(days=10))
    assert evaluate_lot_status(lot) == "conforme"


def test_lot_older_than_365_days_is_perime():
    lot = make_lot(datetime.utcnow() - timedelta(days=400))
    assert evaluate_lot_status(lot) == "périmé"


def test_measurement_within_equateur_thresholds_is_conforme():
    lot = make_lot(datetime.utcnow() - timedelta(days=10))
    measurement = make_measurement(31.0, 60.0)
    assert evaluate_lot_status(lot, measurement) == "conforme"


def test_temperature_out_of_tolerance_is_en_alerte():
    lot = make_lot(datetime.utcnow() - timedelta(days=10))
    measurement = make_measurement(40.0, 60.0)
    assert evaluate_lot_status(lot, measurement) == "en alerte"


def test_humidity_out_of_tolerance_is_en_alerte():
    lot = make_lot(datetime.utcnow() - timedelta(days=10))
    measurement = make_measurement(31.0, 70.0)
    assert evaluate_lot_status(lot, measurement) == "en alerte"


def test_temperature_exact_upper_bound_is_conforme():
    lot = make_lot(datetime.utcnow() - timedelta(days=10))
    measurement = make_measurement(34.0, 60.0)
    assert evaluate_lot_status(lot, measurement) == "conforme"


def test_temperature_just_above_upper_bound_is_en_alerte():
    lot = make_lot(datetime.utcnow() - timedelta(days=10))
    measurement = make_measurement(34.1, 60.0)
    assert evaluate_lot_status(lot, measurement) == "en alerte"


def test_humidity_exact_upper_bound_is_conforme():
    lot = make_lot(datetime.utcnow() - timedelta(days=10))
    measurement = make_measurement(31.0, 62.0)
    assert evaluate_lot_status(lot, measurement) == "conforme"


def test_humidity_just_above_upper_bound_is_en_alerte():
    lot = make_lot(datetime.utcnow() - timedelta(days=10))
    measurement = make_measurement(31.0, 62.1)
    assert evaluate_lot_status(lot, measurement) == "en alerte"


def test_unknown_country_is_conforme():
    lot = make_lot(datetime.utcnow() - timedelta(days=10), country="narnia")
    measurement = make_measurement(999.0, 999.0)
    assert evaluate_lot_status(lot, measurement) == "conforme"
