import json
import os
from datetime import datetime

import paho.mqtt.client as mqtt

from app.database import SessionLocal
from app.models import Lot, Measurement, Alert
from app.email_service import send_grouped_alert_email
from app.thresholds import get_country_thresholds, TEMP_TOLERANCE, HUMIDITY_TOLERANCE

MQTT_HOST = os.getenv("MQTT_HOST", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))

MQTT_TOPIC_MEASURES = os.getenv(
    "MQTT_TOPIC_MEASURES",
    "futurekawa/equateur/measures"
)


def parse_timestamp(value: str):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def build_alert_payload(payload: dict, alert_type: str, value: float, min_value: float, max_value: float):
    direction = "trop basse" if value < min_value else "trop élevée"

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


def save_alert(db, alert_payload: dict):
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

    print(f"Alerte générée par le backend : {alert_payload['message']}", flush=True)


def save_measure(payload: dict):
    db = SessionLocal()

    try:
        generated_alerts = generate_alerts_from_measure(payload)

        lots = (
            db.query(Lot)
            .filter(
                Lot.country == payload["country"],
                Lot.warehouse == payload["warehouse"],
                
            )
            .order_by(Lot.storage_date.asc())
            .all()
        )

        measurement_status = "ALERT" if generated_alerts else "OK"
        parsed_timestamp = parse_timestamp(payload.get("timestamp", datetime.utcnow().isoformat()))

        if lots:
            for lot in lots:
                measurement = Measurement(
                    lot_id=lot.id,
                    country=payload["country"],
                    warehouse=payload["warehouse"],
                    timestamp=parsed_timestamp,
                    temperature=payload["temperature"],
                    humidity=payload["humidity"],
                    status=measurement_status
                )

                db.add(measurement)
                lot.status = "en alerte" if generated_alerts else "conforme"

        else:
            measurement = Measurement(
                lot_id=None,
                country=payload["country"],
                warehouse=payload["warehouse"],
                timestamp=parsed_timestamp,
                temperature=payload["temperature"],
                humidity=payload["humidity"],
                status=measurement_status
            )

            db.add(measurement)

        for alert_payload in generated_alerts:
            save_alert(db, alert_payload)

        db.commit()

        print(
            f"Mesure enregistrée pour {len(lots)} lot(s) "
            f"- {payload['temperature']}°C / {payload['humidity']}% "
            f"- statut {measurement_status}",
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