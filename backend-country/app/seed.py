import random
from datetime import datetime, timedelta

from app.database import SessionLocal
from app.models import Alert, FallbackReading, Lot, Measurement
from app.mqtt_subscriber import generate_alerts_from_measure, save_alert
from app.thresholds import (
    COUNTRY_THRESHOLDS,
    DEFAULT_COUNTRY,
    HUMIDITY_TOLERANCE,
    TEMP_TOLERANCE,
    build_country_lot_code,
    get_own_country,
)

COUNTRY_SEED_DATA = {
    "equateur": {
        "code_prefix": "EQ",
        "warehouses": [
            ("Hacienda Quito", "WH-EQ-01"),
            ("Hacienda Cuenca", "WH-EQ-02"),
        ],
    },
    "bresil": {
        "code_prefix": "BR",
        "warehouses": [
            ("Fazenda Minas Gerais", "WH-BR-01"),
            ("Fazenda Sao Paulo", "WH-BR-02"),
        ],
    },
    "colombie": {
        "code_prefix": "CO",
        "warehouses": [
            ("Finca Huila", "WH-CO-01"),
            ("Finca Narino", "WH-CO-02"),
        ],
    },
}

# (age_days, status, alert_kind) pour chacun des 6 lots seedes, identique
# pour les 3 pays : chaque pays obtient un lot de chaque type (perime,
# alerte temperature, alerte humidite, conforme) - seule la valeur
# ideale/tolerance change selon le pays (voir thresholds.py).
LOT_TEMPLATE = [
    (900, "périmé", None),
    (200, "en alerte", "temperature"),
    (150, "en alerte", "humidity"),
    (100, "conforme", None),
    (45, "conforme", None),
    (10, "conforme", None),
]

HISTORY_POINTS = 15
HISTORY_SPAN_DAYS = 21


def build_lot_code(country: str, index: int) -> str:
    return build_country_lot_code(country, index)


def _history_values(ideal: float, tolerance: float, drift_direction: int | None) -> list[float]:
    values = []

    for point in range(HISTORY_POINTS):
        progress = point / (HISTORY_POINTS - 1)

        if drift_direction:
            offset = progress * (tolerance + 2.5) * drift_direction
        else:
            offset = random.uniform(-tolerance * 0.5, tolerance * 0.5)

        values.append(round(ideal + offset, 1))

    return values


def seed_database():
    random.seed(42)

    country = get_own_country()
    seed_config = COUNTRY_SEED_DATA.get(country, COUNTRY_SEED_DATA[DEFAULT_COUNTRY])
    thresholds = COUNTRY_THRESHOLDS.get(country, COUNTRY_THRESHOLDS[DEFAULT_COUNTRY])

    db = SessionLocal()

    try:
        db.query(Alert).delete(synchronize_session=False)
        db.query(Measurement).delete(synchronize_session=False)
        db.query(Lot).delete(synchronize_session=False)

        now = datetime.utcnow()
        warehouses = seed_config["warehouses"]

        lots = []
        for index, (age_days, status, _alert_kind) in enumerate(LOT_TEMPLATE):
            farm, warehouse = warehouses[index // 3]

            lots.append(Lot(
                lot_code=build_country_lot_code(country, index + 1),
                country=country,
                farm=farm,
                warehouse=warehouse,
                storage_date=now - timedelta(days=age_days),
                status=status,
            ))

        db.add_all(lots)
        db.flush()

        measurements = []
        alerts_to_save = []

        for index, lot in enumerate(lots):
            age_days, _status, alert_kind = LOT_TEMPLATE[index]
            span_days = min(age_days, HISTORY_SPAN_DAYS) or 1

            temp_direction = 1 if alert_kind == "temperature" else None
            humidity_direction = 1 if alert_kind == "humidity" else None

            temperatures = _history_values(thresholds["temperature"], TEMP_TOLERANCE, temp_direction)
            humidities = _history_values(thresholds["humidity"], HUMIDITY_TOLERANCE, humidity_direction)

            for point in range(HISTORY_POINTS):
                timestamp = now - timedelta(days=span_days) + timedelta(
                    days=span_days * point / (HISTORY_POINTS - 1)
                )
                temperature = temperatures[point]
                humidity = humidities[point]

                payload = {
                    "country": country,
                    "warehouse": lot.warehouse,
                    "timestamp": timestamp.isoformat(),
                    "temperature": temperature,
                    "humidity": humidity,
                }
                generated_alerts = generate_alerts_from_measure(payload)

                measurements.append(Measurement(
                    lot_id=lot.id,
                    country=country,
                    warehouse=lot.warehouse,
                    temperature=temperature,
                    humidity=humidity,
                    status="ALERT" if generated_alerts else "OK",
                    source="seed",
                    timestamp=timestamp,
                ))

                if generated_alerts and point == HISTORY_POINTS - 1:
                    alerts_to_save.extend(generated_alerts)

        db.add_all(measurements)

        for alert_payload in alerts_to_save:
            save_alert(db, alert_payload)

        db.commit()

        print(f"Seeder : {len(lots)} lot(s) créé(s) pour {country}.", flush=True)

    finally:
        db.close()


def seed_fallback_readings():
    country = get_own_country()
    seed_config = COUNTRY_SEED_DATA.get(country, COUNTRY_SEED_DATA[DEFAULT_COUNTRY])
    thresholds = COUNTRY_THRESHOLDS.get(country)

    if not thresholds:
        return

    db = SessionLocal()

    try:
        if db.query(FallbackReading).count() > 0:
            return

        readings = [
            FallbackReading(
                country=country,
                warehouse=warehouse,
                temperature=thresholds["temperature"],
                humidity=thresholds["humidity"],
            )
            for _, warehouse in seed_config["warehouses"]
        ]

        db.add_all(readings)
        db.commit()

        print(f"Seeder : {len(readings)} valeur(s) de repli créée(s) pour {country}.", flush=True)

    finally:
        db.close()
