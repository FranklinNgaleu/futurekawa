# Tests FutureKawa

Ce dossier regroupe les trois suites de tests du projet : unitaires, API
(intégration HTTP/MQTT) et UI (Selenium). Les marqueurs pytest et la
configuration commune se trouvent dans `pytest.ini` à la racine du dépôt.

---

## Prérequis

```bash
pip install -r tests/requirements.txt
```

`tests/requirements.txt` couvre les trois suites : `pytest`, `pytest-cov`,
`requests` (tests API), `selenium` + `webdriver-manager` (tests UI),
`sqlalchemy` + `python-dotenv` (tests unitaires).

Pour les tests UI, Google Chrome doit être installé sur la machine (le
driver est téléchargé automatiquement par `webdriver-manager`).

---

## `tests/unit` — Tests unitaires

N'ont besoin d'aucun service externe : ils importent directement le code
Python de `backend-country` et utilisent une base SQLite en mémoire (voir
`tests/unit/conftest.py`, fixture `db_session`). C'est la seule suite dont
la couverture de code (`--cov`) est pleinement représentative du code
applicatif.

```bash
pip install -r backend-country/requirements.txt -r tests/requirements.txt
pytest tests/unit -v
```

---

## `tests/api` — Tests d'intégration API et MQTT

Exécutent des requêtes HTTP réelles contre la stack Docker démarrée
(`backend-country-*`, `backend-central`) et, pour
`test_mqtt_integration.py`, publient de vrais messages MQTT (`paho-mqtt`)
sur les brokers Mosquitto par pays.

```bash
docker compose up -d
pytest tests/api -v
```

URLs et ports par défaut (surchargeables par variable d'environnement) :

| Service | Variable d'environnement | Défaut |
|---------|---------------------------|--------|
| Backend central | `BACKEND_CENTRAL_URL` | `http://localhost:8000` |
| Backend pays (générique) | `BACKEND_COUNTRY_URL` | `http://localhost:8001` |
| Backend pays Équateur | `BACKEND_COUNTRY_EQUATEUR_URL` | `http://localhost:8001` |
| Backend pays Brésil | `BACKEND_COUNTRY_BRESIL_URL` | `http://localhost:8002` |
| Backend pays Colombie | `BACKEND_COUNTRY_COLOMBIE_URL` | `http://localhost:8003` |

Les brokers Mosquitto sont testés directement sur `localhost` aux ports
`1883` (Équateur), `1884` (Brésil) et `1885` (Colombie) — voir
`docker-compose.yml`.

---

## `tests/ui` — Tests Selenium (frontend)

Pilotent Chrome en mode headless contre le frontend servi par
`docker compose`, marqués `@pytest.mark.ui` (voir `pytest.ini`).

```bash
docker compose up -d
pytest tests/ui -v -m ui
```

URL testée : `FRONTEND_URL` (défaut `http://localhost:3000`).

---

## Tout exécuter (comme en CI)

```bash
docker compose up -d
pytest tests/unit tests/api -v
pytest tests/ui -v -m ui
```

C'est l'enchaînement reproduit par les stages "Tests unitaires", "Tests
API/MQTT" et "Tests UI" du `Jenkinsfile`.

---

## Note sur les données de test

Les tests API/UI s'exécutent contre les bases PostgreSQL persistantes de la
stack Docker (pas de réinitialisation automatique entre deux exécutions).
Chaque test crée ses propres lots avec des codes/entrepôts uniques
(`uuid4`) pour rester indépendant des données déjà présentes. Si l'on
modifie manuellement les données de seed pendant des tests manuels
(ex. via `curl`), il est recommandé de relancer `docker compose down -v &&
docker compose up -d` avant de rejouer la suite complète, afin de repartir
d'un jeu de données propre.
