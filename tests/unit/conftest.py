import os
import sys
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

BACKEND_COUNTRY_DIR = Path(__file__).resolve().parents[2] / "backend-country"

if str(BACKEND_COUNTRY_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_COUNTRY_DIR))
