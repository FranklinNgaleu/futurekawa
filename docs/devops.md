# DevOps - FutureKawa

## Présentation

Cette documentation décrit la partie DevOps du projet **FutureKawa**.

L'objectif est de permettre à n'importe quel développeur de lancer rapidement l'application, exécuter les tests et comprendre le pipeline d'intégration continue.

---

# Architecture

Le projet est composé des services suivants :

```
                 Frontend React
                        │
                        ▼
                Backend Central
                        │
        ┌───────────────┴───────────────┐
        ▼                               ▼
 Backend Pays                    PostgreSQL
        │
        ▼
 MQTT Broker (Mosquitto)
        ▲
        │
 Raspberry Pi
```

---

# Conteneurs Docker

Le projet utilise Docker Compose.

Les conteneurs sont :

| Service | Description |
|----------|-------------|
| backend-country | API REST locale du pays |
| backend-central | API siège |
| postgres | Base de données PostgreSQL |
| mosquitto | Broker MQTT |
| frontend | Interface React |

---

# Lancement du projet

Construire les images

```bash
docker compose build
```

Lancer l'ensemble

```bash
docker compose up
```

Lancer en arrière-plan

```bash
docker compose up -d
```

Arrêter

```bash
docker compose down
```

Réinitialiser complètement

```bash
docker compose down -v
docker compose up --build
```

---

# Variables d'environnement

Le backend-country utilise un fichier `.env`.

Variables principales :

```
DATABASE_URL

MQTT_HOST
MQTT_PORT
MQTT_TOPIC_MEASURES

SMTP_HOST
SMTP_PORT
SMTP_USER
SMTP_PASSWORD

ALERT_EMAIL_TO
```

---

# Seeder

Au démarrage :

- création automatique des lots de démonstration
- insertion uniquement si la base est vide

Le seeder permet de disposer immédiatement de données pour les tests et la démonstration.

---

# Scheduler

Au démarrage du backend :

- vérification des dates de stockage
- mise à jour automatique des lots périmés (>365 jours)

Le statut du lot devient :

```
périmé
```

---

# MQTT

Topic principal :

```
futurekawa/equateur/measures
```

Payload :

```json
{
  "country":"equateur",
  "warehouse":"WH-EQ-01",
  "timestamp":"2026-06-30T12:00:00+00:00",
  "temperature":22,
  "humidity":45,
  "status":"OK",
  "alerts":[]
}
```

Le backend :

- reçoit le message
- l'enregistre
- associe les mesures aux lots
- génère les alertes
- envoie un email

---

# Tests

Les tests sont réalisés avec :

- pytest
- requests
- paho-mqtt

Lancer :

```bash
pytest tests/api -v
```

Résultat attendu :

```
9 passed
```

---

# Test MQTT

Le test MQTT vérifie automatiquement :

```
Publication MQTT

↓

Réception du message

↓

Insertion en base

↓

Création des alertes

↓

Consultation via l'API
```

---

# Scripts DevOps

Le dossier scripts contient :

```
scripts/

start.ps1
stop.ps1
reset.ps1
logs.ps1
test.ps1
```

Ils permettent de simplifier les opérations courantes.

---

# Intégration Continue

Le projet contient un Jenkinsfile.

Pipeline :

```
Checkout

↓

Build Docker

↓

Démarrage des services

↓

Tests API

↓

Tests MQTT

↓

Succès / Échec
```

Les tests sont exécutés automatiquement afin de garantir le bon fonctionnement du projet avant toute livraison.

---

# Base de données

Tables principales :

- lots
- measurements
- alerts

Le stockage respecte la logique FIFO grâce au tri sur la date de stockage.

---

# Qualité logicielle

Les bonnes pratiques mises en œuvre :

- Docker
- Docker Compose
- Variables d'environnement
- API REST
- MQTT
- PostgreSQL
- Tests automatisés
- Seeder
- Scheduler
- Documentation
- Pipeline CI/CD (Jenkins)

---

# Auteur

Responsable DevOps :

- Docker
- CI/CD
- Tests automatisés
- MQTT
- Scripts de déploiement
- Documentation technique

Projet MSPR – FutureKawa