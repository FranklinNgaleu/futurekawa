#!/usr/bin/env python3
"""
FutureKawa IoT - Module Équateur
Lecture DHT11 → Vérification seuils → LEDs → Publication MQTT

Auteur : Équipe FutureKawa
"""

import time
import json
import logging
import signal
import sys
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import adafruit_dht
import board

# Import config
sys.path.insert(0, '.')
from config.config import *

# ============================================================
# LOGGING
# ============================================================
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# ============================================================
# GESTION GPIO / LEDs
# ============================================================
def setup_gpio():
    """Initialise les GPIOs en mode BCM."""
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    GPIO.setup(LED_GREEN_PIN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(LED_RED_PIN,   GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(LED_RGB_R_PIN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(LED_RGB_G_PIN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(LED_RGB_B_PIN, GPIO.OUT, initial=GPIO.LOW)

    logger.info("GPIO initialisé (mode BCM)")


def set_leds_ok():
    """Conditions dans les seuils : LED verte ON, rouge OFF, RGB vert."""
    GPIO.output(LED_GREEN_PIN, GPIO.HIGH)
    GPIO.output(LED_RED_PIN,   GPIO.LOW)
    # RGB → vert
    GPIO.output(LED_RGB_R_PIN, GPIO.LOW)
    GPIO.output(LED_RGB_G_PIN, GPIO.HIGH)
    GPIO.output(LED_RGB_B_PIN, GPIO.LOW)


def set_leds_alert():
    """Conditions hors seuils : LED rouge ON, verte OFF, RGB rouge."""
    GPIO.output(LED_GREEN_PIN, GPIO.LOW)
    GPIO.output(LED_RED_PIN,   GPIO.HIGH)
    # RGB → rouge
    GPIO.output(LED_RGB_R_PIN, GPIO.HIGH)
    GPIO.output(LED_RGB_G_PIN, GPIO.LOW)
    GPIO.output(LED_RGB_B_PIN, GPIO.LOW)


def set_leds_connecting():
    """En attente de connexion MQTT : RGB bleu clignotant."""
    GPIO.output(LED_GREEN_PIN, GPIO.LOW)
    GPIO.output(LED_RED_PIN,   GPIO.LOW)
    GPIO.output(LED_RGB_R_PIN, GPIO.LOW)
    GPIO.output(LED_RGB_G_PIN, GPIO.LOW)
    GPIO.output(LED_RGB_B_PIN, GPIO.HIGH)


def set_leds_off():
    """Éteint toutes les LEDs."""
    for pin in [LED_GREEN_PIN, LED_RED_PIN, LED_RGB_R_PIN, LED_RGB_G_PIN, LED_RGB_B_PIN]:
        GPIO.output(pin, GPIO.LOW)


# ============================================================
# MQTT
# ============================================================
mqtt_connected = False


def on_connect(client, userdata, flags, rc):
    global mqtt_connected
    if rc == 0:
        mqtt_connected = True
        logger.info(f"Connecté au broker MQTT ({MQTT_BROKER_HOST}:{MQTT_BROKER_PORT})")
        # Publier un message de statut à la connexion
        client.publish(
            MQTT_TOPIC_STATUS,
            json.dumps({
                "status": "online",
                "country": COUNTRY,
                "warehouse": WAREHOUSE_ID,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }),
            qos=MQTT_QOS,
            retain=True
        )
    else:
        mqtt_connected = False
        logger.error(f"Échec connexion MQTT, code retour : {rc}")


def on_disconnect(client, userdata, rc):
    global mqtt_connected
    mqtt_connected = False
    if rc != 0:
        logger.warning(f"Déconnexion inattendue du broker MQTT (rc={rc}). Tentative de reconnexion...")


def on_publish(client, userdata, mid):
    logger.debug(f"Message publié (mid={mid})")


def setup_mqtt():
    """Crée et configure le client MQTT."""
    client = mqtt.Client(client_id=MQTT_CLIENT_ID, protocol=mqtt.MQTTv311)

    # Auth si configurée
    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    # Message "last will" : si le Pi se déconnecte brutalement
    client.will_set(
        MQTT_TOPIC_STATUS,
        json.dumps({
            "status": "offline",
            "country": COUNTRY,
            "warehouse": WAREHOUSE_ID,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }),
        qos=MQTT_QOS,
        retain=True
    )

    client.on_connect    = on_connect
    client.on_disconnect = on_disconnect
    client.on_publish    = on_publish

    # Reconnexion automatique
    client.reconnect_delay_set(min_delay=2, max_delay=60)

    return client


# ============================================================
# LECTURE DHT11
# ============================================================
def read_dht11(dht_device):
    """
    Lit température et humidité depuis le DHT11.
    Retourne (temperature, humidity) ou (None, None) en cas d'échec.
    """
    for attempt in range(1, DHT_RETRY_COUNT + 1):
        try:
            temperature = dht_device.temperature
            humidity    = dht_device.humidity

            if temperature is not None and humidity is not None:
                logger.debug(f"Lecture DHT11 réussie : {temperature}°C / {humidity}%")
                return round(float(temperature), 1), round(float(humidity), 1)
            else:
                logger.warning(f"Lecture DHT11 incomplète (tentative {attempt}/{DHT_RETRY_COUNT})")

        except RuntimeError as e:
            # Erreur fréquente avec DHT11 (timing) → on réessaie
            logger.warning(f"Erreur lecture DHT11 (tentative {attempt}/{DHT_RETRY_COUNT}) : {e}")

        if attempt < DHT_RETRY_COUNT:
            time.sleep(DHT_RETRY_DELAY)

    logger.error("Impossible de lire le DHT11 après toutes les tentatives")
    return None, None


# ============================================================
# VÉRIFICATION SEUILS
# ============================================================
def check_conditions(temperature, humidity):
    """
    Vérifie si les conditions sont dans les seuils acceptables.
    Retourne (is_ok, alerts[])
    """
    alerts = []

    temp_ok     = TEMP_MIN <= temperature <= TEMP_MAX
    humidity_ok = HUMIDITY_MIN <= humidity <= HUMIDITY_MAX

    if not temp_ok:
        direction = "trop élevée" if temperature > TEMP_MAX else "trop basse"
        alerts.append({
            "type": "TEMPERATURE_OUT_OF_RANGE",
            "message": f"Température {direction} : {temperature}°C (attendu {TEMP_MIN}-{TEMP_MAX}°C)",
            "value": temperature,
            "min": TEMP_MIN,
            "max": TEMP_MAX
        })

    if not humidity_ok:
        direction = "trop élevée" if humidity > HUMIDITY_MAX else "trop basse"
        alerts.append({
            "type": "HUMIDITY_OUT_OF_RANGE",
            "message": f"Humidité {direction} : {humidity}% (attendu {HUMIDITY_MIN}-{HUMIDITY_MAX}%)",
            "value": humidity,
            "min": HUMIDITY_MIN,
            "max": HUMIDITY_MAX
        })

    return (temp_ok and humidity_ok), alerts


# ============================================================
# PUBLICATION MQTT
# ============================================================
def publish_measure(client, temperature, humidity, is_ok, alerts):
    """Publie une mesure sur le topic MQTT."""
    timestamp = datetime.now(timezone.utc).isoformat()

    payload = {
        "country":     COUNTRY,
        "warehouse":   WAREHOUSE_ID,
        "timestamp":   timestamp,
        "temperature": temperature,
        "humidity":    humidity,
        "status":      "OK" if is_ok else "ALERT",
        "alerts":      alerts
    }

    result = client.publish(
        MQTT_TOPIC_MEASURES,
        json.dumps(payload),
        qos=MQTT_QOS
    )

    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        logger.info(
            f"Publié → {MQTT_TOPIC_MEASURES} | "
            f"Temp: {temperature}°C | "
            f"Hum: {humidity}% | "
            f"Status: {'OK' if is_ok else 'ALERTE'}"
        )
    else:
        logger.error(f"Échec publication MQTT (rc={result.rc})")

    # Si alerte, publier aussi sur le topic dédié
    if alerts:
        for alert in alerts:
            alert_payload = {
                "country":   COUNTRY,
                "warehouse": WAREHOUSE_ID,
                "timestamp": timestamp,
                **alert
            }
            client.publish(MQTT_TOPIC_ALERTS, json.dumps(alert_payload), qos=MQTT_QOS)
            logger.warning(f"Alerte publiée : {alert['message']}")


# ============================================================
# ARRÊT PROPRE
# ============================================================
def cleanup(client, dht_device):
    """Nettoyage GPIO et déconnexion MQTT propre."""
    logger.info("Arrêt du module IoT FutureKawa...")
    set_leds_off()

    try:
        client.publish(
            MQTT_TOPIC_STATUS,
            json.dumps({
                "status": "offline",
                "country": COUNTRY,
                "warehouse": WAREHOUSE_ID,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }),
            qos=MQTT_QOS,
            retain=True
        )
        time.sleep(0.5)
        client.disconnect()
    except Exception:
        pass

    try:
        dht_device.exit()
    except Exception:
        pass

    GPIO.cleanup()
    logger.info("Nettoyage terminé. À bientôt.")


# ============================================================
# MAIN
# ============================================================
def main():
    logger.info("=" * 50)
    logger.info(f"FutureKawa IoT - Démarrage ({COUNTRY.upper()})")
    logger.info(f"Entrepôt : {WAREHOUSE_ID}")
    logger.info(f"Seuils : Temp {TEMP_MIN}-{TEMP_MAX}°C | Hum {HUMIDITY_MIN}-{HUMIDITY_MAX}%")
    logger.info("=" * 50)

    # Init GPIO
    setup_gpio()
    set_leds_connecting()

    # Init DHT11 (GPIO4 = board.D4)
    dht_device = adafruit_dht.DHT11(board.D4)

    # Init MQTT
    client = setup_mqtt()

    # Gestion Ctrl+C / SIGTERM
    def signal_handler(sig, frame):
        cleanup(client, dht_device)
        sys.exit(0)

    signal.signal(signal.SIGINT,  signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Connexion MQTT (avec retry)
    logger.info(f"Connexion au broker MQTT {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}...")
    try:
        client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_KEEPALIVE)
    except Exception as e:
        logger.error(f"Impossible de joindre le broker MQTT : {e}")
        logger.info("Le module continuera à tenter de se reconnecter...")

    client.loop_start()

    # Boucle principale
    logger.info(f"Démarrage des relevés toutes les {READING_INTERVAL_SECONDS}s")

    while True:
        temperature, humidity = read_dht11(dht_device)

        if temperature is not None and humidity is not None:
            is_ok, alerts = check_conditions(temperature, humidity)

            # Mise à jour LEDs
            if is_ok:
                set_leds_ok()
            else:
                set_leds_alert()

            # Publication MQTT
            if mqtt_connected:
                publish_measure(client, temperature, humidity, is_ok, alerts)
            else:
                logger.warning("MQTT non connecté, mesure non publiée (sera retentée au prochain cycle)")
                set_leds_connecting()

        else:
            # Erreur de lecture : LEDs en mode erreur (RGB bleu)
            set_leds_connecting()
            logger.error("Mesure ignorée (erreur capteur)")

        time.sleep(READING_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
