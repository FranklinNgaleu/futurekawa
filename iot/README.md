# FutureKawa IoT — Module Équateur 🇪🇨

Module IoT du projet FutureKawa pour l'entrepôt Équateur.  
Il lit la température/humidité via un DHT11, contrôle des LEDs selon l'état,
et publie les mesures sur un broker MQTT.

---

## Matériel requis

| Composant | Quantité |
|-----------|----------|
| Raspberry Pi 3 | 1 |
| Capteur DHT11 (module S/V/G) | 1 |
| LED verte | 1 |
| LED rouge | 1 |
| LED RGB (cathode commune) | 1 |
| Résistances 330Ω | 5 |
| Breadboard | 1 |
| Câbles dupont | - |

---

## Câblage (GPIO BCM)

```
DHT11 (module)
  S  → GPIO4  (Pin 7)
  V  → 3.3V   (Pin 1)
  G  → GND    (Pin 6)

LED verte
  +  → Résistance 330Ω → GPIO17 (Pin 11)
  -  → GND (Pin 9)

LED rouge
  +  → Résistance 330Ω → GPIO27 (Pin 13)
  -  → GND (Pin 14)

LED RGB (cathode commune)
  R  → Résistance 330Ω → GPIO22 (Pin 15)
  G  → Résistance 330Ω → GPIO23 (Pin 16)
  B  → Résistance 330Ω → GPIO24 (Pin 18)
  -  → GND (Pin 20)
```

---

## Comportement des LEDs

| Situation | LED verte | LED rouge | LED RGB |
|-----------|-----------|-----------|---------|
| Conditions OK | ✅ ON | ❌ OFF | 🟢 Vert |
| Conditions hors seuils | ❌ OFF | ✅ ON | 🔴 Rouge |
| MQTT non connecté / erreur capteur | ❌ OFF | ❌ OFF | 🔵 Bleu |

---

## Seuils Équateur

| Paramètre | Idéal | Min acceptable | Max acceptable |
|-----------|-------|----------------|----------------|
| Température | 31°C | 28°C | 34°C |
| Humidité | 60% | 58% | 62% |

---

## Installation

```bash
# 1. Cloner / copier les fichiers sur le Raspberry Pi

# 2. Lancer l'installation des dépendances
chmod +x install.sh
./install.sh

# 3. Configurer l'IP du broker MQTT
nano config/config.py
# → Modifier MQTT_HOST avec l'IP du broker Mosquitto dédié au pays du module
# (ou définir les variables d'environnement MQTT_HOST / MQTT_PORT au lancement)
```

---

## Lancement

```bash
python3 iot_main.py
```

Les logs s'affichent dans le terminal ET sont sauvegardés dans `logs/iot.log`.

---

## Topics MQTT publiés

| Topic | Contenu |
|-------|---------|
| `futurekawa/equateur/measures` | Mesures temp/humidité + statut |
| `futurekawa/equateur/alerts` | Alertes déclenchées |
| `futurekawa/equateur/status` | Statut online/offline du module |

### Exemple de payload `measures`

```json
{
  "country": "equateur",
  "warehouse": "WH-EQ-01",
  "timestamp": "2026-05-27T10:30:00+00:00",
  "temperature": 32.5,
  "humidity": 61.0,
  "status": "OK",
  "alerts": []
}
```

### Exemple de payload en cas d'alerte

```json
{
  "country": "equateur",
  "warehouse": "WH-EQ-01",
  "timestamp": "2026-05-27T10:30:00+00:00",
  "temperature": 36.0,
  "humidity": 61.0,
  "status": "ALERT",
  "alerts": [
    {
      "type": "TEMPERATURE_OUT_OF_RANGE",
      "message": "Température trop élevée : 36.0°C (attendu 28-34°C)",
      "value": 36.0,
      "min": 28.0,
      "max": 34.0
    }
  ]
}
```

---

## Arrêt propre

`Ctrl+C` ou `kill` → le module publie un statut `offline` avant de s'arrêter et nettoie les GPIO.
