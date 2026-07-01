# Architecture Technique

```
                      React

                        │

                        ▼

               Backend Central

                        │

       ┌────────────────┴────────────────┐

       ▼                                 ▼

Backend Country                    PostgreSQL

       │

       ▼

 MQTT Broker (Mosquitto)

       ▲

       │

 Raspberry Pi
```

---

## Backend Country

Responsabilités :

- gestion des lots
- mesures MQTT
- alertes
- emails
- FIFO

---

## Backend Central

Responsabilités :

- consolidation des données
- dashboard
- consultation des pays

---

## MQTT

Topic principal :

```
futurekawa/equateur/measures
```

Le Raspberry Pi publie les mesures.

Le backend-country est abonné au topic.

---

## Base de données

Tables :

- lots
- measurements
- alerts
