# Plan de tests — FutureKawa

## Objectif

Ce document décrit la stratégie de tests mise en place pour vérifier le bon fonctionnement de la solution FutureKawa.

Les tests couvrent principalement :

- les APIs REST ;
- le backend country ;
- le backend central ;
- le flux MQTT ;
- la génération des alertes.

---

## Typologie des tests

| Type de test | Objectif | Statut |
|---|---|---|
| Tests unitaires | Vérifier une fonction isolée | Partiel |
| Tests API | Vérifier les endpoints REST | Réalisé |
| Tests d’intégration | Vérifier plusieurs composants ensemble | Réalisé |
| Tests MQTT | Vérifier le flux IoT → backend | Réalisé |
| Tests UI | Vérifier l’interface React | À réaliser |
| Tests end-to-end | Vérifier un scénario utilisateur complet | À réaliser |

---

## Outils utilisés

- `pytest` : exécution des tests automatisés ;
- `requests` : appels HTTP vers les APIs ;
- `paho-mqtt` : publication de messages MQTT de test ;
- Docker Compose : environnement de test complet.

---

## Commandes de test

Installer les dépendances :

```bash
pip install -r tests/requirements.txt
```

Lancer tous les tests :

```bash
pytest tests/api -v
```

Résultat attendu :

```text
9 passed
```

---

## Données de test

Les données de test sont générées automatiquement par le seeder du backend country.

Lots créés :

| Lot | Pays | Exploitation | Entrepôt |
|---|---|---|---|
| LOT-EQ-001 | equateur | Hacienda Quito | WH-EQ-01 |
| LOT-EQ-002 | equateur | Hacienda Quito | WH-EQ-01 |
| LOT-EQ-003 | equateur | Hacienda Quito | WH-EQ-01 |
| LOT-EQ-004 | equateur | Hacienda Cuenca | WH-EQ-02 |
| LOT-EQ-005 | equateur | Hacienda Cuenca | WH-EQ-02 |
| LOT-EQ-006 | equateur | Hacienda Cuenca | WH-EQ-02 |

Ces lots permettent de tester :

- le FIFO ;
- les mesures par entrepôt ;
- les alertes ;
- les statuts des lots.

---

## Cas de test API — Backend Country

| ID | Cas de test | Endpoint | Critère de réussite |
|---|---|---|---|
| TC-BC-01 | Vérifier l’état du backend country | `GET /health` | Code 200 + statut healthy |
| TC-BC-02 | Récupérer les lots | `GET /lots` | Code 200 + liste JSON |
| TC-BC-03 | Récupérer les mesures | `GET /measurements` | Code 200 + liste JSON |
| TC-BC-04 | Récupérer les alertes | `GET /alerts` | Code 200 + liste JSON |

---

## Cas de test API — Backend Central

| ID | Cas de test | Endpoint | Critère de réussite |
|---|---|---|---|
| TC-CEN-01 | Vérifier l’état du backend central | `GET /health` | Code 200 + statut healthy |
| TC-CEN-02 | Récupérer les pays | `GET /countries` | Code 200 + clé countries |
| TC-CEN-03 | Récupérer le dashboard | `GET /dashboard` | Code 200 + clé statistics |
| TC-CEN-04 | Récupérer les alertes consolidées | `GET /alerts` | Code 200 + clé alerts |

---

## Cas de test MQTT

| ID | Cas de test | Objectif | Critère de réussite |
|---|---|---|---|
| TC-MQTT-01 | Publier une mesure MQTT | Vérifier la réception par le backend | Mesure visible via API |
| TC-MQTT-02 | Publier une mesure hors seuil | Vérifier la génération d’alerte | Alertes créées |
| TC-MQTT-03 | Mesure sur un entrepôt | Vérifier l’association aux lots | Mesure liée aux lots concernés |

Payload MQTT de test :

```json
{
  "country": "equateur",
  "warehouse": "WH-EQ-01",
  "timestamp": "2026-06-30T12:00:00+00:00",
  "temperature": 22,
  "humidity": 45,
  "status": "OK",
  "alerts": []
}
```

---

## Critères de réussite globaux

Un test est considéré comme réussi si :

- l’API répond avec un code HTTP attendu ;
- le format JSON est conforme ;
- les données sont correctement persistées ;
- les alertes sont générées lorsque les seuils sont dépassés ;
- le flux MQTT fonctionne de bout en bout.

---

## Gestion des anomalies

La gestion des anomalies suit le processus suivant :

1. Constat de l’anomalie.
2. Identification du composant concerné.
3. Analyse des logs Docker.
4. Correction du code ou de la configuration.
5. Rebuild Docker.
6. Relance des tests.
7. Validation après correction.

Exemple :

| Anomalie | Cause | Correction | Re-test |
|---|---|---|---|
| Erreur PostgreSQL au démarrage | Backend lancé avant la base | Ajout d’un healthcheck | Relance Docker |
| SMTP non configuré | Variables `.env` non chargées | Ajout `env_file` | Test MQTT + email |
| Mesure non liée au lot | Filtre entrepôt/statut incorrect | Correction du subscriber | Test MQTT |

---

## Tests UI et end-to-end

Le frontend React étant disponible, des tests complémentaires peuvent être réalisés.

### Scénarios UI

| ID | Scénario | Critère de réussite |
|---|---|---|
| TC-UI-01 | Affichage du dashboard | Les KPI lots, mesures et alertes sont visibles |
| TC-UI-02 | Sélection du pays Équateur | Les lots du pays s’affichent |
| TC-UI-03 | Consultation d’un lot | Les informations du lot sont visibles |
| TC-UI-04 | Affichage des courbes | Les courbes température/humidité s’affichent |
| TC-UI-05 | Affichage des alertes | Les alertes sont listées avec message et seuils |

### Scénario end-to-end

| ID | Scénario | Critère de réussite |
|---|---|---|
| TC-E2E-01 | Publier une mesure MQTT hors seuil | La mesure est stockée, une alerte est générée et visible dans le frontend |
| TC-E2E-02 | Consulter un lot impacté | Le lot affiche le statut `en alerte` et ses mesures |

---

## Conclusion

La stratégie de tests permet de valider les composants essentiels du projet :

- APIs REST ;
- communication MQTT ;
- persistance des mesures ;
- génération des alertes ;
- consolidation par le backend central.

