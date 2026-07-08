# CI / CD

Le projet utilise Jenkins pour automatiser les opérations.

Pipeline :

```
GitHub

↓

Checkout

↓

Docker Build

↓

Docker Compose Up

↓

Tests API

↓

Tests MQTT

↓

Résultat
```

---

## Jenkinsfile

Le pipeline :

- récupère le projet
- construit les images Docker
- démarre les services
- lance les tests
- arrête les services

---

## Tests

Les tests utilisent :

- pytest
- requests
- paho-mqtt

Commande :

```bash
pytest tests/api -v
```

Résultat attendu :

```
9 passed
```
