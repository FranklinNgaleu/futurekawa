import json
import os
from datetime import datetime

import paho.mqtt.client as mqtt

from app.database import SessionLocal
from app.models import Lot, Measurement, Alert

MQTT_HOST = os.getenv("MQTT_HOST", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))

MQTT_TOPIC_MEASURES = os.getenv(
    "MQTT_TOPIC_MEASURES",
    "futurekawa/equateur/measures"
)

MQTT_TOPIC_ALERTS = os.getenv(
    "MQTT_TOPIC_ALERTS",
    "futurekawa/equateur/alerts"
)


def parse_timestamp(value: str):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def save_measure(payload):
    db = SessionLocal()

    try:
        lot = (
            db.query(Lot)
            .filter(
                Lot.country == payload["country"],
                Lot.warehouse == payload["warehouse"],
                Lot.status != "périmé"
            )
            .order_by(Lot.storage_date.asc())
            .first()
        )

        measurement = Measurement(
            lot_id=lot.id if lot else None,
            country=payload["country"],
            warehouse=payload["warehouse"],
            timestamp=parse_timestamp(payload["timestamp"]),
            temperature=payload["temperature"],
            humidity=payload["humidity"],
            status=payload.get("status", "OK")
        )

        db.add(measurement)

        if lot:
            lot.status = "en alerte" if payload.get("status") == "ALERT" else "conforme"

        db.commit()

        print(f"Mesure MQTT enregistrée - lot associé : {lot.id if lot else 'Aucun'}")

    except Exception as e:
        db.rollback()
        print(f"Erreur sauvegarde mesure MQTT : {e}")

    finally:
        db.close()


def save_alert(payload):
    db = SessionLocal()

    try:
        alert = Alert(
            country=payload["country"],
            warehouse=payload["warehouse"],
            timestamp=parse_timestamp(payload["timestamp"]),
            type=payload["type"],
            message=payload["message"],
            value=payload["value"],
            min=payload.get("min"),
            max=payload.get("max")
        )

        db.add(alert)

        lot = (
            db.query(Lot)
            .filter(
                Lot.country == payload["country"],
                Lot.warehouse == payload["warehouse"],
                Lot.status != "périmé"
            )
            .order_by(Lot.storage_date.asc())
            .first()
        )

        if lot:
            lot.status = "en alerte"

        db.commit()

        print(f"Alerte MQTT enregistrée : {payload['message']}")

    except Exception as e:
        db.rollback()
        print(f"Erreur sauvegarde alerte MQTT : {e}")

    finally:
        db.close()


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connecté au broker MQTT")

        client.subscribe(MQTT_TOPIC_MEASURES)
        client.subscribe(MQTT_TOPIC_ALERTS)

        print(f"Abonné à {MQTT_TOPIC_MEASURES}")
        print(f"Abonné à {MQTT_TOPIC_ALERTS}")
    else:
        print("Erreur connexion MQTT :", rc)


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())

        if msg.topic == MQTT_TOPIC_MEASURES:
            save_measure(payload)

        elif msg.topic == MQTT_TOPIC_ALERTS:
            save_alert(payload)

    except Exception as e:
        print(f"Erreur traitement MQTT : {e}")


def start_mqtt_subscriber():
    client = mqtt.Client()

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_HOST, MQTT_PORT, 60)

    client.loop_start()