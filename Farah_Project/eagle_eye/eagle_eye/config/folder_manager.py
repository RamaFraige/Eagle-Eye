from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent

HOME_DIR = ROOT_DIR / "data"

# weights
WEIGHTS_DIR = HOME_DIR / "weights"

# Store directories
MEDIA_DIR = HOME_DIR / "media"
DB_DIR = HOME_DIR / "db"
SQL_DIR = DB_DIR / "sql"
VECTOR_DIR = DB_DIR / "vector"


ALL_DIRS = [HOME_DIR, MEDIA_DIR, DB_DIR, SQL_DIR, VECTOR_DIR, WEIGHTS_DIR]


for dir in ALL_DIRS:
    dir.mkdir(exist_ok=True, parents=True)
