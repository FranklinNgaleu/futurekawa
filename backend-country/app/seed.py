import os
from datetime import datetime, timedelta

from app.database import SessionLocal
from app.models import FallbackReading, Lot
from app.thresholds import COUNTRY_THRESHOLDS, normalize_country

DEFAULT_COUNTRY = "equateur"

# (lot suffix, farm, warehouse) per warehouse, in seeding order
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

# Age (in days) of each of the 6 seeded lots, oldest first (3 per warehouse)
LOT_AGE_DAYS = [920, 750, 500, 300, 170, 20]


def get_active_country():
    return normalize_country(os.getenv("COUNTRY", DEFAULT_COUNTRY))


def seed_database():
    country = get_active_country()
    seed_config = COUNTRY_SEED_DATA.get(country, COUNTRY_SEED_DATA[DEFAULT_COUNTRY])

    db = SessionLocal()

    try:
        if db.query(Lot).count() > 0:
            print("Seeder : lots déjà présents.", flush=True)
            return

        now = datetime.utcnow()
        code_prefix = seed_config["code_prefix"]
        warehouses = seed_config["warehouses"]

        lots = []
        for index, age_days in enumerate(LOT_AGE_DAYS):
            farm, warehouse = warehouses[index // 3]
            storage_date = now - timedelta(days=age_days)

            lots.append(Lot(
                lot_code=f"LOT-{code_prefix}-{index + 1:03d}",
                country=country,
                farm=farm,
                warehouse=warehouse,
                storage_date=storage_date,
                status="périmé" if age_days > 365 else "conforme",
            ))

        db.add_all(lots)
        db.commit()

        print(f"Seeder : {len(lots)} lot(s) créé(s) pour {country}.", flush=True)

    finally:
        db.close()


def seed_fallback_readings():
    country = get_active_country()
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
