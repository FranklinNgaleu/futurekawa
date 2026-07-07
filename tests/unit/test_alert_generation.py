import pytest

from app.mqtt_subscriber import build_alert_payload, generate_alerts_from_measure

COUNTRY_THRESHOLDS = {
    "bresil": {"temperature": 29, "humidity": 55},
    "equateur": {"temperature": 31, "humidity": 60},
    "colombie": {"temperature": 26, "humidity": 80},
}
TEMP_TOLERANCE = 3
HUMIDITY_TOLERANCE = 2


def make_payload(country, temperature, humidity):
    return {
        "country": country,
        "warehouse": "WH-EQ-01",
        "timestamp": "2026-01-01T00:00:00",
        "temperature": temperature,
        "humidity": humidity,
    }


def test_measure_within_thresholds_generates_no_alert():
    payload = make_payload("equateur", 31.0, 60.0)
    assert generate_alerts_from_measure(payload) == []


def test_temperature_too_low_generates_one_alert_labelled_trop_basse():
    payload = make_payload("equateur", 20.0, 60.0)
    alerts = generate_alerts_from_measure(payload)

    assert len(alerts) == 1
    assert alerts[0]["type"] == "TEMPERATURE_OUT_OF_RANGE"
    assert "trop basse" in alerts[0]["message"]


def test_temperature_too_high_generates_one_alert_labelled_trop_elevee():
    payload = make_payload("equateur", 40.0, 60.0)
    alerts = generate_alerts_from_measure(payload)

    assert len(alerts) == 1
    assert alerts[0]["type"] == "TEMPERATURE_OUT_OF_RANGE"
    assert "trop élevée" in alerts[0]["message"]


def test_both_out_of_range_generates_two_alerts():
    payload = make_payload("equateur", 40.0, 90.0)
    alerts = generate_alerts_from_measure(payload)

    assert len(alerts) == 2
    assert {a["type"] for a in alerts} == {
        "TEMPERATURE_OUT_OF_RANGE",
        "HUMIDITY_OUT_OF_RANGE",
    }


@pytest.mark.parametrize("country", ["bresil", "equateur", "colombie"])
def test_country_bounds_are_correct(country):
    thresholds = COUNTRY_THRESHOLDS[country]
    payload = make_payload(country, thresholds["temperature"] + 100, thresholds["humidity"])

    alerts = generate_alerts_from_measure(payload)

    assert len(alerts) == 1
    assert alerts[0]["min"] == thresholds["temperature"] - TEMP_TOLERANCE
    assert alerts[0]["max"] == thresholds["temperature"] + TEMP_TOLERANCE


def test_unknown_country_generates_no_alert():
    payload = make_payload("narnia", 999.0, 999.0)
    assert generate_alerts_from_measure(payload) == []


def test_build_alert_payload_trop_basse():
    payload = make_payload("equateur", 20.0, 60.0)
    result = build_alert_payload(payload, "TEMPERATURE_OUT_OF_RANGE", 20.0, 28, 34)

    assert "trop basse" in result["message"]
    assert result["min"] == 28
    assert result["max"] == 34
    assert result["value"] == 20.0


def test_build_alert_payload_trop_elevee():
    payload = make_payload("equateur", 40.0, 60.0)
    result = build_alert_payload(payload, "TEMPERATURE_OUT_OF_RANGE", 40.0, 28, 34)

    assert "trop élevée" in result["message"]
