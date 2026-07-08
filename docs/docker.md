# Docker

Le projet est entièrement conteneurisé.

## Services

- backend-country
- backend-central
- postgres
- mosquitto
- frontend

---

## Commandes

Construire

```bash
docker compose build
```

Démarrer

```bash
docker compose up
```

Arrière-plan

```bash
docker compose up -d
```

Arrêter

```bash
docker compose down
```

Logs

```bash
docker compose logs
```

Rebuild

```bash
docker compose up --build
```

---

## Variables d'environnement

backend-country/.env

```
DATABASE_URL
MQTT_HOST
MQTT_PORT

SMTP_HOST
SMTP_PORT
SMTP_USER
SMTP_PASSWORD
ALERT_EMAIL_TO
```
