from datetime import datetime, timedelta

from app.database import SessionLocal
from app.models import Alert, Lot
from app.email_service import send_alert_email

LOT_EXPIRATION_DAYS = 365


def check_expired_lots():
    db = SessionLocal()

    try:
        now = datetime.utcnow()
        expiration_limit = now - timedelta(days=LOT_EXPIRATION_DAYS)

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
            age_days = (now - lot.storage_date).days

            alert_payload = {
                "country": lot.country,
                "warehouse": lot.warehouse,
                "timestamp": now.isoformat(),
                "type": "LOT_EXPIRED",
                "message": (
                    f"Lot {lot.lot_code} périmé : stocké le "
                    f"{lot.storage_date.strftime('%Y-%m-%d')} ({age_days} jours)"
                ),
                "value": age_days,
                "min": None,
                "max": LOT_EXPIRATION_DAYS,
            }

            db.add(Alert(
                country=alert_payload["country"],
                warehouse=alert_payload["warehouse"],
                timestamp=now,
                type=alert_payload["type"],
                message=alert_payload["message"],
                value=alert_payload["value"],
                min=alert_payload["min"],
                max=alert_payload["max"],
            ))

            send_alert_email(alert_payload)

        db.commit()

        print(f"Scheduler : {len(expired_lots)} lot(s) marqué(s) comme périmé(s).", flush=True)

    except Exception as e:
        db.rollback()
        print(f"Erreur scheduler lots périmés : {e}", flush=True)

    finally:
        db.close()