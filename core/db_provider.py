"""Database service selector.

Exposes :func:`get_database_service` which returns a ready‑to‑use
:class:`DatabaseService` instance based on the deployment *ENVIRONMENT*
setting ("prod" or "test").

The configs are expected to live in :pymod:`ids.core.config` alongside this module.
"""
from __future__ import annotations

from typing import Final

from .config import ENVIRONMENT, postgres_config, sqlite_config
from .db_factory import DatabaseFactory, DatabaseService

__all__: Final = ["get_database_service"]


def get_database_service() -> DatabaseService:  # noqa: D401
    """Return a :class:`DatabaseService` configured for the current environment.

    * ``ENVIRONMENT == 'prod'`` → PostgreSQL
    * ``ENVIRONMENT == 'test'`` → SQLite (typically an in‑memory DB)
    """
    if ENVIRONMENT == "prod":
        db = DatabaseFactory.create_database(postgres_config)
        return DatabaseService(db)

    if ENVIRONMENT == "test":
        db = DatabaseFactory.create_database(sqlite_config)
        return DatabaseService(db)

    raise ValueError("ENVIRONMENT must be 'prod' or 'test'")
