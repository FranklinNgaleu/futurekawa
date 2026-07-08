from app.email_service import resolve_alert_email_to


def test_resolver_uses_country_specific_address_for_bresil(monkeypatch):
    monkeypatch.setenv("ALERT_EMAIL_TO", "siege@futurekawa.example")
    monkeypatch.setenv("ALERT_EMAIL_TO_BRESIL", "bresil@futurekawa.example")

    assert resolve_alert_email_to("bresil") == "bresil@futurekawa.example"


def test_resolver_uses_country_specific_address_for_equateur(monkeypatch):
    monkeypatch.setenv("ALERT_EMAIL_TO", "siege@futurekawa.example")
    monkeypatch.setenv("ALERT_EMAIL_TO_EQUATEUR", "equateur@futurekawa.example")

    assert resolve_alert_email_to("equateur") == "equateur@futurekawa.example"


def test_resolver_uses_country_specific_address_for_colombie(monkeypatch):
    monkeypatch.setenv("ALERT_EMAIL_TO", "siege@futurekawa.example")
    monkeypatch.setenv("ALERT_EMAIL_TO_COLOMBIE", "colombie@futurekawa.example")

    assert resolve_alert_email_to("colombie") == "colombie@futurekawa.example"


def test_resolver_falls_back_to_generic_address_when_country_specific_not_set(monkeypatch):
    monkeypatch.setenv("ALERT_EMAIL_TO", "siege@futurekawa.example")
    monkeypatch.delenv("ALERT_EMAIL_TO_BRESIL", raising=False)

    assert resolve_alert_email_to("bresil") == "siege@futurekawa.example"


def test_resolver_falls_back_to_own_country_when_none_given(monkeypatch):
    monkeypatch.setenv("COUNTRY", "equateur")
    monkeypatch.setenv("ALERT_EMAIL_TO_EQUATEUR", "equateur@futurekawa.example")

    assert resolve_alert_email_to() == "equateur@futurekawa.example"
