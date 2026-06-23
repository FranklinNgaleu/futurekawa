import json
import os
from datetime import datetime
import paho.mqtt.client as mqtt

from app.database import SessionLocal
from app.models import Measurement

MQTT_HOST = os.getenv("MQTT_HOST", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC_MEASURES = os.getenv("MQTT_TOPIC_MEASURES", "futurekawa/equateur/measures")


def save_measure(payload: dict):
    db = SessionLocal()

    try:
        measurement = Measurement(
            lot_id=None,
            country=payload["country"],
            warehouse=payload["warehouse"],
            timestamp=datetime.fromisoformat(payload["timestamp"]),
            temperature=payload["temperature"],
            humidity=payload["humidity"],
            status=payload.get("status", "OK")
        )

        db.add(measurement)
        db.commit()

        print(f"Mesure MQTT enregistrée : {payload}")

    except Exception as e:
        db.rollback()
        print(f"Erreur sauvegarde MQTT : {e}")

    finally:
        db.close()


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connecté au broker MQTT")
        client.subscribe(MQTT_TOPIC_MEASURES)
        print(f"Abonné au topic : {MQTT_TOPIC_MEASURES}")
    else:
        print(f"Erreur connexion MQTT : {rc}")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        save_measure(payload)
    except Exception as e:
        print(f"Erreur traitement message MQTT : {e}")


def start_mqtt_subscriber():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_start()