from pathlib import Path


APP_NAME = "summary-app-backend"
APP_VERSION = "0.1.0"

BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
USAGE_DB_PATH = DATA_DIR / "usage.db"

FREE_LIMIT = 2

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
