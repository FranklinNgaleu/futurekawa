import json
import os
from datetime import datetime

import paho.mqtt.client as mqtt

from app.database import SessionLocal
from app.models import Lot, Measurement, Alert
from app.email_service import send_alert_email
from app.email_service import send_grouped_alert_email

MQTT_HOST = os.getenv("MQTT_HOST", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))

MQTT_TOPIC_MEASURES = os.getenv(
    "MQTT_TOPIC_MEASURES",
    "futurekawa/equateur/measures"
)

COUNTRY_THRESHOLDS = {
    "bresil": {"temperature": 29, "humidity": 55},
    "brésil": {"temperature": 29, "humidity": 55},
    "equateur": {"temperature": 31, "humidity": 60},
    "équateur": {"temperature": 31, "humidity": 60},
    "colombie": {"temperature": 26, "humidity": 80},
}

TEMP_TOLERANCE = 3
HUMIDITY_TOLERANCE = 2


def parse_timestamp(value: str):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def get_country_thresholds(country: str):
    return COUNTRY_THRESHOLDS.get(country.lower())


def build_alert_payload(payload: dict, alert_type: str, value: float, min_value: float, max_value: float):
    if value < min_value:
        direction = "trop basse"
    else:
        direction = "trop élevée"

    if alert_type == "TEMPERATURE_OUT_OF_RANGE":
        label = "Température"
        unit = "°C"
    else:
        label = "Humidité"
        unit = "%"

    return {
        "country": payload["country"],
        "warehouse": payload["warehouse"],
        "timestamp": payload["timestamp"],
        "type": alert_type,
        "message": f"{label} {direction} : {value}{unit} (attendu {min_value}-{max_value}{unit})",
        "value": value,
        "min": min_value,
        "max": max_value,
    }


def generate_alerts_from_measure(payload: dict):
    thresholds = get_country_thresholds(payload["country"])

    if not thresholds:
        return []

    temp_min = thresholds["temperature"] - TEMP_TOLERANCE
    temp_max = thresholds["temperature"] + TEMP_TOLERANCE

    humidity_min = thresholds["humidity"] - HUMIDITY_TOLERANCE
    humidity_max = thresholds["humidity"] + HUMIDITY_TOLERANCE

    alerts = []

    temperature = payload["temperature"]
    humidity = payload["humidity"]

    if temperature < temp_min or temperature > temp_max:
        alerts.append(
            build_alert_payload(
                payload,
                "TEMPERATURE_OUT_OF_RANGE",
                temperature,
                temp_min,
                temp_max
            )
        )

    if humidity < humidity_min or humidity > humidity_max:
        alerts.append(
            build_alert_payload(
                payload,
                "HUMIDITY_OUT_OF_RANGE",
                humidity,
                humidity_min,
                humidity_max
            )
        )

    return alerts


def save_alert(db, alert_payload: dict, lot: Lot | None = None):
    alert = Alert(
        country=alert_payload["country"],
        warehouse=alert_payload["warehouse"],
        timestamp=parse_timestamp(alert_payload["timestamp"]),
        type=alert_payload["type"],
        message=alert_payload["message"],
        value=alert_payload["value"],
        min=alert_payload.get("min"),
        max=alert_payload.get("max")
    )

    db.add(alert)

    if lot:
        lot.status = "en alerte"

    print(f"Alerte générée par le backend : {alert_payload['message']}", flush=True)


def save_measure(payload: dict):
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

        generated_alerts = generate_alerts_from_measure(payload)

        measurement = Measurement(
            lot_id=lot.id if lot else None,
            country=payload["country"],
            warehouse=payload["warehouse"],
            timestamp=parse_timestamp(payload["timestamp"]),
            temperature=payload["temperature"],
            humidity=payload["humidity"],
            status="ALERT" if generated_alerts else "OK"
        )

        db.add(measurement)

        if lot:
            lot.status = "en alerte" if generated_alerts else "conforme"

        for alert_payload in generated_alerts:
            save_alert(db, alert_payload, lot)

        db.commit()

        print(
            f"Mesure enregistrée : {payload['temperature']}°C / {payload['humidity']}% "
            f"- statut {measurement.status}",
            flush=True
        )

        if generated_alerts:
            send_grouped_alert_email(generated_alerts)

    except Exception as e:
        db.rollback()
        print(f"Erreur sauvegarde mesure MQTT : {e}", flush=True)

    finally:
        db.close()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connecté au broker MQTT", flush=True)
        client.subscribe(MQTT_TOPIC_MEASURES)
        print(f"Abonné à {MQTT_TOPIC_MEASURES}", flush=True)
    else:
        print("Erreur connexion MQTT :", rc, flush=True)


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())

        if msg.topic == MQTT_TOPIC_MEASURES:
            save_measure(payload)

    except Exception as e:
        print(f"Erreur traitement MQTT : {e}", flush=True)


def start_mqtt_subscriber():
    client = mqtt.Client()

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_HOST, MQTT_PORT, 60)

    client.loop_start()