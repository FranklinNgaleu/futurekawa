from datetime import datetime

from app.database import SessionLocal
from app.models import Lot


def seed_database():
    db = SessionLocal()

    try:
        # Ne rien faire si des lots existent déjà
        if db.query(Lot).count() > 0:
            print("Seeder : lots déjà présents.", flush=True)
            return

        lots = [
            Lot(
                lot_code="LOT-EQ-001",
                country="equateur",
                farm="Hacienda Quito",
                warehouse="WH-EQ-01",
                storage_date=datetime(2024, 1, 10, 8, 0, 0),
                status="périmé"
            ),
            Lot(
                lot_code="LOT-EQ-002",
                country="equateur",
                farm="Hacienda Quito",
                warehouse="WH-EQ-01",
                storage_date=datetime(2024, 6, 18, 9, 30, 0),
                status="conforme"
            ),
            Lot(
                lot_code="LOT-EQ-003",
                country="equateur",
                farm="Hacienda Quito",
                warehouse="WH-EQ-01",
                storage_date=datetime(2025, 2, 15, 10, 15, 0),
                status="conforme"
            ),
            Lot(
                lot_code="LOT-EQ-004",
                country="equateur",
                farm="Hacienda Cuenca",
                warehouse="WH-EQ-02",
                storage_date=datetime(2025, 9, 1, 14, 0, 0),
                status="conforme"
            ),
            Lot(
                lot_code="LOT-EQ-005",
                country="equateur",
                farm="Hacienda Cuenca",
                warehouse="WH-EQ-02",
                storage_date=datetime(2026, 1, 12, 11, 20, 0),
                status="conforme"
            ),
            Lot(
                lot_code="LOT-EQ-006",
                country="equateur",
                farm="Hacienda Cuenca",
                warehouse="WH-EQ-02",
                storage_date=datetime(2026, 6, 20, 16, 45, 0),
                status="conforme"
            ),
        ]

        db.add_all(lots)
        db.commit()

        print("Seeder : 6 lots créés.", flush=True)

    finally:
        db.close()