#!/bin/bash
# ============================================================
# FutureKawa IoT - Installation des dépendances
# À lancer UNE seule fois sur le Raspberry Pi
# ============================================================

echo "=== FutureKawa IoT - Installation ==="

# Mise à jour du système
sudo apt-get update -y

# Dépendances système pour adafruit-dht
sudo apt-get install -y python3-pip python3-dev libgpiod2

# Librairies Python
pip3 install \
    adafruit-circuitpython-dht \
    paho-mqtt \
    RPi.GPIO

echo ""
echo "=== Installation terminée ==="
echo "Édite config/config.py pour configurer l'IP du broker MQTT,"
echo "puis lance : python3 iot_main.py"
