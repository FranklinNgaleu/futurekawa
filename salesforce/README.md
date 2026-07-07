# FutureKawa - Module Salesforce

## Prérequis

- Salesforce CLI (`sf`)
- Un Dev Hub ou un scratch org / sandbox authentifié
- L'URL réelle du endpoint configurée dans le Named Credential `FutureKawa_API` après déploiement

## Déploiement

```
sf org login web --alias futurekawa
sf project deploy start --source-dir force-app --target-org futurekawa
sf apex run test --target-org futurekawa --code-coverage --result-format human
```
