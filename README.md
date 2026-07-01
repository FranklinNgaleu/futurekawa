# ☕ FutureKawa

FutureKawa est une plateforme IoT permettant de surveiller les conditions de stockage des lots de café dans plusieurs pays producteurs.

Le système collecte les mesures de température et d'humidité via des capteurs connectés (Raspberry Pi), les transmet via MQTT puis les centralise afin de superviser les stocks et générer automatiquement des alertes.

---

# Fonctionnalités

- Gestion des lots de café
- Gestion des entrepôts
- Surveillance IoT (température / humidité)
- Communication MQTT
- Alertes automatiques
- Envoi automatique d'emails
- Gestion FIFO des lots
- Backend central de supervision
- Dashboard Web
- Docker & Docker Compose
- Tests automatisés
- Pipeline CI/CD (Jenkins)

---

# Architecture

```text
                 Frontend React
                        │
                        ▼
               Backend Central
                        │
        ┌───────────────┴───────────────┐
        ▼                               ▼
 Backend Country                 PostgreSQL
        │
        ▼
 MQTT Broker (Mosquitto)
        ▲
        │
 Raspberry Pi
```

---

# Technologies utilisées

## Backend

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL

## IoT

- Raspberry Pi
- MQTT
- Mosquitto
- Paho MQTT

## Frontend

- React
- Chart.js

## DevOps

- Docker
- Docker Compose
- Jenkins
- Pytest

---

# Installation

## Cloner le projet

```bash
git clone <url-du-projet>
cd FutureKawa
```

## Construire les images

```bash
docker compose build
```

## Lancer les services

```bash
docker compose up
```

---

# Documentation

La documentation technique est disponible dans le dossier **docs/**.

| Document | Description |
|----------|-------------|
| database-architecture.md | Architecture de la base de données |
| frontend-api.md | Documentation API pour le frontend |
| devops.md | Documentation DevOps |
| ci-cd.md | Pipeline CI/CD |
| docker.md | Déploiement Docker |

---

# Organisation des branches Git

Le projet utilise Git Flow simplifié.

| Branche | Description |
|----------|-------------|
| main | Version stable |
| develop | Branche d'intégration |
| feature/* | Développement des fonctionnalités |

### Répartition de l'équipe

| Branche | Responsable | Description |
|----------|-------------|-------------|
| feature/backend-country | Dev 1 | Backend pays (API REST, PostgreSQL, MQTT, alertes) |
| feature/backend-central | Dev 2 | Backend siège (consolidation des données) |
| feature/frontend | Dev 3 | Interface Web React |
| feature/iot-mqtt | Dev 4 | Raspberry Pi, MQTT, capteurs |
| feature/devops-ci | Dev 5 | Docker, Jenkins, tests, CI/CD |

---

# Lancement des tests

Installer les dépendances :

```bash
pip install -r tests/requirements.txt
```

Lancer tous les tests :

```bash
pytest tests/api -v
```

Les tests couvrent :

- Backend Country
- Backend Central
- API REST
- MQTT (test d'intégration)

---

# Pipeline CI/CD

Le projet contient un **Jenkinsfile** permettant d'automatiser :

- récupération du code
- build Docker
- démarrage des services
- exécution des tests
- arrêt des conteneurs

---

# Auteurs

Projet réalisé dans le cadre de la MSPR.

| Développeur | Responsabilités |
|-------------|-----------------|
| Dev 1 | Backend Country |
| Dev 2 | Backend Central |
| Dev 3 | Frontend |
| Dev 4 | IoT / MQTT |
| Dev 5 | DevOps, Docker, CI/CD, Tests |

---

