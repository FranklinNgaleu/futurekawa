import os

COUNTRY_THRESHOLDS = {
    "bresil": {"temperature": 29, "humidity": 55},
    "equateur": {"temperature": 31, "humidity": 60},
    "colombie": {"temperature": 26, "humidity": 80},
}

TEMP_TOLERANCE = 3
HUMIDITY_TOLERANCE = 2

DEFAULT_COUNTRY = "equateur"

COUNTRY_CODE_PREFIXES = {
    "equateur": "EQ",
    "bresil": "BR",
    "colombie": "CO",
}

ACCENT_MAP = str.maketrans("éèêà", "eeea")


def normalize_country(country: str) -> str:
    return country.strip().lower().translate(ACCENT_MAP)


def get_country_thresholds(country: str):
    return COUNTRY_THRESHOLDS.get(normalize_country(country))


def get_own_country() -> str:
    return normalize_country(os.getenv("COUNTRY", DEFAULT_COUNTRY))


def get_country_code_prefix(country: str) -> str:
    normalized = normalize_country(country)
    return COUNTRY_CODE_PREFIXES.get(normalized, COUNTRY_CODE_PREFIXES[DEFAULT_COUNTRY])


def build_country_lot_code(country: str, suffix: str | int) -> str:
    prefix = get_country_code_prefix(country)
    if isinstance(suffix, int):
        suffix = f"{suffix:03d}"
    return f"LOT-{prefix}-{suffix}"
