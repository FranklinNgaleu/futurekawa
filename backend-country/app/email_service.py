import os
import smtplib
from email.message import EmailMessage

from app.thresholds import get_own_country

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT") or "587")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

COUNTRY_EMAIL_ENV_SUFFIXES = {
    "bresil": "BRESIL",
    "equateur": "EQUATEUR",
    "colombie": "COLOMBIE",
}


def resolve_alert_email_to(country: str = None) -> str:
    country = country or get_own_country()
    suffix = COUNTRY_EMAIL_ENV_SUFFIXES.get(country)

    if suffix:
        specific = os.getenv(f"ALERT_EMAIL_TO_{suffix}")
        if specific:
            return specific

    return os.getenv("ALERT_EMAIL_TO")


def send_alert_email(alert_payload: dict):
    alert_email_to = resolve_alert_email_to(alert_payload.get("country"))

    if not SMTP_USER or not SMTP_PASSWORD or not alert_email_to:
        print("Email non envoyé : configuration SMTP manquante")
        return

    msg = EmailMessage()
    msg["Subject"] = f"[FutureKawa] Alerte {alert_payload['type']} - {alert_payload['warehouse']}"
    msg["From"] = SMTP_USER
    msg["To"] = alert_email_to

    msg.set_content(f"""
Bonjour,

Une alerte a été détectée.

Pays : {alert_payload['country']}
Entrepôt : {alert_payload['warehouse']}
Type : {alert_payload['type']}
Message : {alert_payload['message']}
Valeur : {alert_payload['value']}
Min : {alert_payload.get('min')}
Max : {alert_payload.get('max')}
Date : {alert_payload['timestamp']}



FutureKawa - Team

Merci!
""")

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        print(f"Email d'alerte envoyé à {alert_email_to}")

    except Exception as e:
        print(f"Erreur envoi email : {e}")


def send_grouped_alert_email(alerts: list[dict]):
    if not alerts:
        return

    first_alert = alerts[0]
    alert_email_to = resolve_alert_email_to(first_alert.get("country"))

    if not SMTP_USER or not SMTP_PASSWORD or not alert_email_to:
        print("Email non envoyé : configuration SMTP manquante", flush=True)
        return

    subject = f"[FutureKawa] Alerte stockage - {first_alert['warehouse']}"

    alert_lines = []

    for alert in alerts:
        alert_lines.append(
            f"""
- Type : {alert['type']}
  Message : {alert['message']}
  Valeur : {alert['value']}
  Min : {alert.get('min')}
  Max : {alert.get('max')}
"""
        )

    body = f"""
Bonjour,

Une ou plusieurs alertes ont été détectées dans l'entrepôt {first_alert['warehouse']}.

Pays : {first_alert['country']}
Entrepôt : {first_alert['warehouse']}
Date : {first_alert['timestamp']}

Détails des alertes :
{''.join(alert_lines)}

Merci de vérifier les conditions de stockage.

FutureKawa - Team

Merci!
"""

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = alert_email_to
    msg.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        print(f"Email groupé d'alerte envoyé à {alert_email_to}", flush=True)

    except Exception as e:
        print(f"Erreur envoi email groupé : {e}", flush=True)
