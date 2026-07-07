# ============================================================
# FutureKawa IoT - Configuration Équateur
# ============================================================

# --- Pays / Entrepôt ---
COUNTRY = "equateur"
WAREHOUSE_ID = "WH-EQ-01"

# --- Conditions idéales pour l'Équateur ---
IDEAL_TEMP = 31.0       # °C
IDEAL_HUMIDITY = 60.0   # %
TOLERANCE_TEMP = 3.0    # ±3°C
TOLERANCE_HUMIDITY = 2.0  # ±2%

# Seuils calculés
TEMP_MIN = IDEAL_TEMP - TOLERANCE_TEMP       # 28°C
TEMP_MAX = IDEAL_TEMP + TOLERANCE_TEMP       # 34°C
HUMIDITY_MIN = IDEAL_HUMIDITY - TOLERANCE_HUMIDITY  # 58%
HUMIDITY_MAX = IDEAL_HUMIDITY + TOLERANCE_HUMIDITY  # 62%

# --- GPIO Pins (BCM numbering) ---
DHT_PIN = 4          # GPIO4  → Pin 7  (capteur DHT11, broche S)
LED_GREEN_PIN = 17   # GPIO17 → Pin 11 (conditions OK)
LED_RED_PIN = 27     # GPIO27 → Pin 13 (conditions hors plage)
LED_RGB_R_PIN = 22   # GPIO22 → Pin 15 (LED RGB rouge)
LED_RGB_G_PIN = 23   # GPIO23 → Pin 16 (LED RGB vert)
LED_RGB_B_PIN = 24   # GPIO24 → Pin 18 (LED RGB bleu)

# --- MQTT ---
MQTT_BROKER_HOST = "192.168.1.17"
MQTT_BROKER_PORT = 1883
MQTT_USERNAME = None
MQTT_PASSWORD = None
MQTT_CLIENT_ID = f"futurekawa-iot-{COUNTRY}"
MQTT_QOS = 1
MQTT_KEEPALIVE = 60

# Topics MQTT
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
