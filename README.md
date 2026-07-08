## 🌳 Organisation des branches Git

Le projet utilise une stratégie Git simple basée sur :

- `main` → version stable du projet
- `develop` → branche d’intégration globale
- `feature/*` → branches de développement par fonctionnalité

### Branches de l’équipe

| Branche | Responsable | Description |
|---|---|---|
| `feature/backend-country` | Dev 1 | Backend local pays (API REST, DB, alertes) |
| `feature/backend-central` | Dev 2 | Backend central siège (consolidation des données) |
| `feature/frontend` | Dev 3 | Interface Web (dashboard, graphiques, consultation lots) |
| `feature/iot-mqtt` | Dev 4 | IoT, MQTT, capteurs, publication des données |
| `feature/devops-ci` | Dev 5 | Docker, CI/CD Jenkins, tests, infrastructure |

---

## 🚀 Démarrage

### Prérequis

- Docker et Docker Compose v2 (`docker compose`, sans tiret).
- Python 3.11+ si l'on souhaite lancer les tests en dehors de Jenkins.

### Lancer la stack complète

```bash
cp .env.example .env
# Renseigner au minimum les variables SMTP/ALERT_EMAIL_TO_* dans .env
# si l'envoi d'emails d'alerte doit être testé.

docker compose up -d --build
```

Services exposés une fois la stack démarrée (healthchecks visibles via
`docker compose ps`) :

| Service | URL / port | Rôle |
|---------|------------|------|
| Frontend | http://localhost:3000 | Interface web (dashboard, lots, vue siège) |
| Backend central | http://localhost:8000 | API de consolidation multi-pays |
| Backend pays Équateur | http://localhost:8001 | API locale Équateur |
| Backend pays Brésil | http://localhost:8002 | API locale Brésil |
| Backend pays Colombie | http://localhost:8003 | API locale Colombie |
| PostgreSQL | localhost:5432 | Une base par pays (`futurekawa_equateur/bresil/colombie`) |
| Mosquitto Équateur | localhost:1883 | Broker MQTT dédié Équateur |
| Mosquitto Brésil | localhost:1884 | Broker MQTT dédié Brésil |
| Mosquitto Colombie | localhost:1885 | Broker MQTT dédié Colombie |

### Arrêter / réinitialiser la stack

```bash
docker compose down        # arrête les conteneurs, conserve les données
docker compose down -v     # arrête et supprime aussi les volumes (repart de zéro)
```

### Lancer les tests

Voir `tests/README.md` pour le détail complet (prérequis, variables
d'environnement par service, suites unitaires/API/UI).

```bash
pip install -r tests/requirements.txt
pytest tests/unit tests/api -v      # nécessite la stack démarrée pour tests/api
pytest tests/ui -v -m ui            # nécessite en plus Google Chrome installé
```

### Module IoT

Le code du module IoT (Raspberry Pi, hors périmètre matériel de ce dépôt)
et sa documentation se trouvent dans `iot/` (voir `iot/README.md`).

---