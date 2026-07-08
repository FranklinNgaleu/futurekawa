import os
import random
from datetime import datetime, timedelta

from app.database import SessionLocal
from app.models import FallbackReading, Measurement
from app.mqtt_subscriber import apply_measurement
from app.email_service import send_grouped_alert_email

FALLBACK_STALE_AFTER_MINUTES = int(os.getenv("FALLBACK_STALE_AFTER_MINUTES", "15"))
FALLBACK_JITTER_TEMP = 0.5
FALLBACK_JITTER_HUMIDITY = 1.0


def jittered(value, spread):
    return round(value + random.uniform(-spread, spread), 1)


def is_stale(last_timestamp, now, stale_after_minutes):
    if last_timestamp is None:
        return True
    return last_timestamp < now - timedelta(minutes=stale_after_minutes)


def apply_fallback_measurements():
    db = SessionLocal()

    try:
        now = datetime.utcnow()
        all_generated_alerts = []
        warehouses_updated = 0

        for reading in db.query(FallbackReading).all():
            last_measurement = (
                db.query(Measurement)
                .filter(
                    Measurement.country == reading.country,
                    Measurement.warehouse == reading.warehouse,
                )
                .order_by(Measurement.timestamp.desc())
                .first()
            )

            last_timestamp = last_measurement.timestamp if last_measurement else None

            if not is_stale(last_timestamp, now, FALLBACK_STALE_AFTER_MINUTES):
                continue

            generated_alerts, _ = apply_measurement(
                db,
                country=reading.country,
                warehouse=reading.warehouse,
                temperature=jittered(reading.temperature, FALLBACK_JITTER_TEMP),
                humidity=jittered(reading.humidity, FALLBACK_JITTER_HUMIDITY),
                timestamp=now,
                source="fallback",
            )

            all_generated_alerts.extend(generated_alerts)
            warehouses_updated += 1

        db.commit()

        if warehouses_updated:
            print(
                f"Fallback : {warehouses_updated} entrepôt(s) sans donnée IoT récente, "
                f"valeur(s) de repli appliquée(s).",
                flush=True
            )

        if all_generated_alerts:
            send_grouped_alert_email(all_generated_alerts)

    except Exception as e:
        db.rollback()
        print(f"Erreur application des valeurs de repli : {e}", flush=True)

    finally:
        db.close()
