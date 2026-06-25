from datetime import datetime, timedelta

from app.database import SessionLocal
from app.models import Lot


def check_expired_lots():
    db = SessionLocal()

    try:
        expiration_limit = datetime.utcnow() - timedelta(days=365)

        expired_lots = (
            db.query(Lot)
            .filter(
                Lot.storage_date < expiration_limit,
                Lot.status != "périmé"
            )
            .all()
        )

        for lot in expired_lots:
            lot.status = "périmé"

        db.commit()

        print(f"Scheduler : {len(expired_lots)} lot(s) marqué(s) comme périmé(s).", flush=True)

    except Exception as e:
        db.rollback()
        print(f"Erreur scheduler lots périmés : {e}", flush=True)

    finally:
        db.close()