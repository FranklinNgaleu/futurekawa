COUNTRY_THRESHOLDS = {
    "bresil": {"temperature": 29, "humidity": 55},
    "equateur": {"temperature": 31, "humidity": 60},
    "colombie": {"temperature": 26, "humidity": 80},
}

TEMP_TOLERANCE = 3
HUMIDITY_TOLERANCE = 2

ACCENT_MAP = str.maketrans("éèêà", "eeea")


def normalize_country(country: str) -> str:
    return country.strip().lower().translate(ACCENT_MAP)


def get_country_thresholds(country: str):
    return COUNTRY_THRESHOLDS.get(normalize_country(country))
