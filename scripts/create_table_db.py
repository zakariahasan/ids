from pathlib import Path
from ids.core.config import DB_DSN              # supplies the DSN string
from ids.core.db import DatabaseClient          # your wrapper around psycopg2 / asyncpg

# ---------------------------------------------------------------------------
# Dynamic project paths
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents.parents   # .../ids/
SQL_DIR  = BASE_DIR / "queries"                 # .../ids/queries

DROP_SQL_PATH   = SQL_DIR / "drop_tables.sql"
CREATE_SQL_PATH = SQL_DIR / "create_tables.sql"

# ---------------------------------------------------------------------------
# Run the scripts
# ---------------------------------------------------------------------------

with DatabaseClient(DB_DSN) as db:              # auto-close even on error
    db.execute_sql_from_file(DROP_SQL_PATH)     # ← pass the *path*
    db.execute_sql_from_file(CREATE_SQL_PATH)
