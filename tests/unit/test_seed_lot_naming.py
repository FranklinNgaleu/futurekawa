import pytest

from app.seed import build_lot_code


@pytest.mark.parametrize(
    ("country", "index", "expected"),
    [
        ("equateur", 1, "LOT-EQ-001"),
        ("bresil", 2, "LOT-BR-002"),
        ("colombie", 3, "LOT-CO-003"),
    ],
)
def test_build_lot_code_uses_country_prefix(country, index, expected):
    assert build_lot_code(country, index) == expected
