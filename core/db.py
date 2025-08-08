"""Compatibility shim for legacy `from ids.core.db import db` imports.

Going forward, all code should use:

    from ids.core.db_provider import get_database_service
    db = get_database_service()

This stub keeps the project running while the remaining files are migrated.
"""

from .db_provider import get_database_service as _get_db

# Singleton service – created lazily the first time `db` is accessed.
db = _get_db()
