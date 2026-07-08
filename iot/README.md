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

## Seuils par pays

Le module IoT peut être déployé pour n'importe lequel des trois pays du
projet : régler la variable d'environnement `COUNTRY` (`equateur`, `bresil`
ou `colombie`) sélectionne automatiquement les seuils correspondants dans
`config/config.py` (tolérance fixe de ±3°C / ±2% autour de l'idéal, identique
au calcul côté `backend-country/app/thresholds.py`).

| Pays | Idéal | Tolérance | Min acceptable | Max acceptable | Entrepôt par défaut |
|------|-------|-----------|-----------------|-----------------|----------------------|
| Équateur | 31°C / 60% | ±3°C / ±2% | 28°C / 58% | 34°C / 62% | `WH-EQ-01` |
| Brésil | 29°C / 55% | ±3°C / ±2% | 26°C / 53% | 32°C / 57% | `WH-BR-01` |
| Colombie | 26°C / 80% | ±3°C / ±2% | 23°C / 78% | 29°C / 82% | `WH-CO-01` |

---

## Fréquence des relevés

Le module lit le capteur DHT11 et publie une mesure toutes les
`READING_INTERVAL_SECONDS` (5 secondes par défaut, voir `config/config.py`).
En cas d'échec de lecture du capteur, jusqu'à `DHT_RETRY_COUNT` tentatives
(3 par défaut) sont effectuées avec `DHT_RETRY_DELAY` secondes d'attente
entre chaque tentative, avant d'abandonner le cycle courant.

---

## Reconnexion MQTT et message "Last Will" (LWT)

- **Reconnexion automatique** : le client MQTT (`paho-mqtt`) est configuré
  avec `reconnect_delay_set(min_delay=2, max_delay=60)` : en cas de perte de
  connexion au broker, il retente avec un délai croissant de 2s jusqu'à 60s,
  sans intervention manuelle.
- **Last Will and Testament (LWT)** : avant de se connecter, le module
  enregistre un message `will_set(...)` sur le topic `futurekawa/<pays>/status`
  avec `{"status": "offline", ...}` (retained). Si le module se déconnecte
  brutalement (coupure réseau, crash, coupure d'alimentation) sans fermeture
  propre, le broker Mosquitto publie automatiquement ce message à la place du
  module — le siège est ainsi notifié même en cas de panne matérielle.
- **Statut "online"** : à la connexion réussie, le module publie lui-même un
  message `{"status": "online", ...}` (retained) sur le même topic.
- **Arrêt propre** : sur `Ctrl+C`/`SIGTERM`, le module publie explicitement
  `{"status": "offline", ...}` puis se déconnecte proprement (voir
  section "Arrêt propre" plus bas), sans attendre le déclenchement du LWT.
- **Mesures non publiées si déconnecté** : tant que `mqtt_connected` est
  `False`, les mesures lues ne sont pas publiées (elles sont simplement
  perdues, pas mises en file d'attente) ; le cycle suivant retentera une
  publication dès que la connexion sera rétablie. C'est le mécanisme de
  fallback côté `backend-country` (voir ci-dessous) qui compense les mesures
  manquantes en cas de coupure prolongée.

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

Chaque pays dispose de son propre broker Mosquitto (`mosquitto-equateur`,
`mosquitto-bresil`, `mosquitto-colombie` dans `docker-compose.yml`, ports
1883/1884/1885) : les noms de topics restent inchangés d'un broker à
l'autre, seul le broker cible (`MQTT_HOST`/`MQTT_PORT`) change selon le pays
du module.

| Topic | Contenu |
|-------|---------|
| `futurekawa/equateur/measures` | Mesures temp/humidité + statut |
| `futurekawa/equateur/alerts` | Alertes déclenchées |
| `futurekawa/equateur/status` | Statut online/offline du module |

(Remplacer `equateur` par `bresil` ou `colombie` selon la variable
`COUNTRY` du module concerné.)

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

## Tâches planifiées côté backend (complément)

Le module IoT ne fait que lire et publier : c'est `backend-country` qui
complète les données en cas de coupure via deux tâches planifiées
(APScheduler), configurables par variables d'environnement du service :

| Tâche | Variable d'environnement | Fréquence par défaut | Rôle |
|-------|---------------------------|------------------------|------|
| Vérification des lots périmés | `EXPIRED_LOTS_CHECK_INTERVAL_MINUTES` | 60 min | Repasse le statut des lots en `périmé` au-delà d'un an de stockage. |
| Mesures de secours (fallback) | `FALLBACK_CHECK_INTERVAL_MINUTES` | 5 min | Génère une mesure de repli par entrepôt si aucune mesure IoT récente n'a été reçue (voir `FALLBACK_STALE_AFTER_MINUTES`, 15 min par défaut = seuil au-delà duquel un entrepôt est considéré "silencieux"). |

Ce mécanisme de secours est ce qui garantit la continuité du monitoring
lorsque le module IoT est déconnecté du broker MQTT plus longtemps que
`FALLBACK_STALE_AFTER_MINUTES` (voir la section précédente sur le LWT).

---

## Arrêt propre

`Ctrl+C` ou `kill` → le module publie un statut `offline` avant de s'arrêter et nettoie les GPIO.
