import json
import time
from datetime import datetime, timezone

import requests
import paho.mqtt.client as mqtt

COUNTRY_BROKERS = {
    "equateur": {"mqtt_port": 1883, "api_url": "http://localhost:8001", "warehouse": "WH-EQ-01"},
    "bresil": {"mqtt_port": 1884, "api_url": "http://localhost:8002", "warehouse": "WH-BR-01"},
}

MQTT_HOST = "localhost"


def publish_measurement_and_assert_alerts(country, temperature, humidity):
    config = COUNTRY_BROKERS[country]
    timestamp = datetime.now(timezone.utc).isoformat()

    payload = {
        "country": country,
        "warehouse": config["warehouse"],
        "timestamp": timestamp,
        "temperature": temperature,
        "humidity": humidity,
        "status": "OK",
        "alerts": []
    }

    client = mqtt.Client()
    client.connect(MQTT_HOST, config["mqtt_port"], 60)
    client.publish(f"futurekawa/{country}/measures", json.dumps(payload))
    client.disconnect()

    time.sleep(3)

    measurements_response = requests.get(f"{config['api_url']}/measurements", params={"limit": 500})
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

    alerts_response = requests.get(f"{config['api_url']}/alerts")
    assert alerts_response.status_code == 200

    alerts = alerts_response.json()

    matching_alerts = [
        a for a in alerts
        if a["warehouse"] == payload["warehouse"]
        and a["timestamp"].startswith(timestamp[:19])
    ]

    return [a["type"] for a in matching_alerts]


def test_mqtt_measure_creates_expected_measurement_and_alerts():
    alert_types = publish_measurement_and_assert_alerts("equateur", temperature=25.0, humidity=46.0)

    assert "TEMPERATURE_OUT_OF_RANGE" in alert_types
    assert "HUMIDITY_OUT_OF_RANGE" in alert_types


def test_mqtt_measure_on_bresil_broker_creates_no_alert_when_within_range():
    alert_types = publish_measurement_and_assert_alerts("bresil", temperature=29.0, humidity=55.0)

    assert "TEMPERATURE_OUT_OF_RANGE" not in alert_types
    assert "HUMIDITY_OUT_OF_RANGE" not in alert_types