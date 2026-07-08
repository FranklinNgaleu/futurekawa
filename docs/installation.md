# Installation - FutureKawa

## Prérequis

- Docker Desktop
- Docker Compose
- Python 3.11+
- Git

---

## Cloner le projet

```bash
git clone <url-du-projet>
cd FutureKawa
```

---

## Construire les images

```bash
docker compose build
```

---

## Lancer les services

```bash
docker compose up
```

---

## Arrêter les services

```bash
docker compose down
```

---

## Réinitialiser complètement

```bash
docker compose down -v
docker compose up --build
```

---

## Accès aux services

| Service | URL |
|----------|-----|
| Backend Country | http://localhost:8001/docs |
| Backend Central | http://localhost:8000/docs |
| Frontend | http://localhost:3000 |
| PostgreSQL | localhost:5432 |
| MQTT | localhost:1883 |

---

## Données de démonstration

Le seeder crée automatiquement :

- 6 lots
- 2 entrepôts
- données prêtes pour les tests
