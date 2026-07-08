# ============================================================
# FutureKawa IoT - Configuration
# ============================================================
# Un même module IoT peut être déployé pour n'importe quel pays :
# régler les variables d'environnement COUNTRY / WAREHOUSE_ID sur le Pi.

import os

# --- Conditions idéales par pays (miroir de backend-country/app/thresholds.py) ---
COUNTRY_THRESHOLDS = {
    "bresil":   {"temperature": 29.0, "humidity": 55.0, "default_warehouse": "WH-BR-01"},
    "equateur": {"temperature": 31.0, "humidity": 60.0, "default_warehouse": "WH-EQ-01"},
    "colombie": {"temperature": 26.0, "humidity": 80.0, "default_warehouse": "WH-CO-01"},
}

TOLERANCE_TEMP = 3.0      # ±3°C
TOLERANCE_HUMIDITY = 2.0  # ±2%

# --- Pays / Entrepôt ---
COUNTRY = os.environ.get("COUNTRY", "equateur").lower()

if COUNTRY not in COUNTRY_THRESHOLDS:
    COUNTRY = "equateur"

_country_config = COUNTRY_THRESHOLDS[COUNTRY]

WAREHOUSE_ID = os.environ.get("WAREHOUSE_ID", _country_config["default_warehouse"])

# --- Conditions idéales pour le pays configuré ---
IDEAL_TEMP = _country_config["temperature"]        # °C
IDEAL_HUMIDITY = _country_config["humidity"]        # %

# Seuils calculés
TEMP_MIN = IDEAL_TEMP - TOLERANCE_TEMP
TEMP_MAX = IDEAL_TEMP + TOLERANCE_TEMP
HUMIDITY_MIN = IDEAL_HUMIDITY - TOLERANCE_HUMIDITY
HUMIDITY_MAX = IDEAL_HUMIDITY + TOLERANCE_HUMIDITY

# --- GPIO Pins (BCM numbering) ---
DHT_PIN = 4          # GPIO4  → Pin 7  (capteur DHT11, broche S)
LED_GREEN_PIN = 17   # GPIO17 → Pin 11 (conditions OK)
LED_RED_PIN = 27     # GPIO27 → Pin 13 (conditions hors plage)
LED_RGB_R_PIN = 22   # GPIO22 → Pin 15 (LED RGB rouge)
LED_RGB_G_PIN = 23   # GPIO23 → Pin 16 (LED RGB vert)
LED_RGB_B_PIN = 24   # GPIO24 → Pin 18 (LED RGB bleu)

# --- MQTT ---
MQTT_BROKER_HOST = os.environ.get("MQTT_BROKER_HOST", "192.168.1.17")
MQTT_BROKER_PORT = int(os.environ.get("MQTT_BROKER_PORT", "1883"))
MQTT_USERNAME = os.environ.get("MQTT_USERNAME") or None
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD") or None
MQTT_CLIENT_ID = f"futurekawa-iot-{COUNTRY}-{WAREHOUSE_ID}"
MQTT_QOS = 1
MQTT_KEEPALIVE = 60

# Topics MQTT (un topic par pays, partagé par tous les entrepôts de ce pays)
MQTT_TOPIC_MEASURES = f"futurekawa/{COUNTRY}/measures"
MQTT_TOPIC_ALERTS   = f"futurekawa/{COUNTRY}/alerts"
MQTT_TOPIC_STATUS   = f"futurekawa/{COUNTRY}/status"

# --- Fréquence de relevé ---
READING_INTERVAL_SECONDS = 5
DHT_RETRY_COUNT = 3
DHT_RETRY_DELAY = 2

# --- Logs ---
LOG_FILE = "logs/iot.log"
LOG_LEVEL = "INFO"
