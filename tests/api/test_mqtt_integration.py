import json
import time
from datetime import datetime, timezone

import requests
import paho.mqtt.client as mqtt

MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "futurekawa/equateur/measures"

COUNTRY_API_URL = "http://localhost:8001"


def test_mqtt_measure_creates_expected_measurement_and_alerts():
    timestamp = datetime.now(timezone.utc).isoformat()

    payload = {
        "country": "equateur",
        "warehouse": "WH-EQ-01",
        "timestamp": timestamp,
        "temperature": 25.0,
        "humidity": 46.0,
        "status": "OK",
        "alerts": []
    }

    client = mqtt.Client()
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.publish(MQTT_TOPIC, json.dumps(payload))
    client.disconnect()

    time.sleep(3)

    measurements_response = requests.get(f"{COUNTRY_API_URL}/measurements")
    assert measurements_response.status_code == 200

    measurements = measurements_response.json()

    matching_measurements = [
        m for m in measurements
        if m["warehouse"] == payload["warehouse"]
        and m["temperature"] == payload["temperature"]
        and m["humidity"] == payload["humidity"]
        and m["timestamp"].startswith(timestamp[:19])
    ]

    assert len(matching_measurements) > 0

    alerts_response = requests.get(f"{COUNTRY_API_URL}/alerts")
    assert alerts_response.status_code == 200

    alerts = alerts_response.json()

    matching_alerts = [
        a for a in alerts
        if a["warehouse"] == payload["warehouse"]
        and a["timestamp"].startswith(timestamp[:19])
    ]

    alert_types = [a["type"] for a in matching_alerts]

    assert "TEMPERATURE_OUT_OF_RANGE" in alert_types
    assert "HUMIDITY_OUT_OF_RANGE" in alert_types