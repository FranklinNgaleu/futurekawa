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