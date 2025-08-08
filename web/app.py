"""
ids.web.app – Flask entry-point

The database URI is selected automatically:

  * ENVIRONMENT == "prod"  ➜ Postgres  (ids/core/config.postgres_config)
  * ENVIRONMENT == "test"  ➜ SQLite    (ids/core/config.sqlite_config)

Override at runtime with the IDS_ENV environment variable.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping, Final

from flask import Flask, redirect, url_for

from ids.web.extensions import db
from ids.web.routes import register_blueprints
from ids.core import config as core_cfg  # re-use the central config

# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #


def _build_db_uri(env: str) -> str:
    """Return an SQLAlchemy-compatible DB-URI for *env* (“prod” / “test”)."""
    if env == "prod":
        cfg: Mapping[str, str] = core_cfg.postgres_config
        return (
            f"postgresql://{cfg['user']}:{cfg['password']}"
            f"@{cfg['host']}/{cfg['dbname']}"
        )

    if env == "test":
        db_path = Path(core_cfg.sqlite_config["db_path"])
        db_path.parent.mkdir(parents=True, exist_ok=True)  # first run
        return f"sqlite:///{db_path.as_posix()}"

    raise ValueError("ENVIRONMENT must be 'prod' or 'test'")


# --------------------------------------------------------------------------- #
# Factory                                                                     #
# --------------------------------------------------------------------------- #


def create_app() -> Flask:
    """Flask application factory."""
    env: Final[str] = os.getenv("IDS_ENV", core_cfg.ENVIRONMENT)
    db_uri = _build_db_uri(env)

    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("IDS_SECRET_KEY", "devkey"),
        SQLALCHEMY_DATABASE_URI=db_uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    db.init_app(app)
    register_blueprints(app)

    @app.route("/")  # default root → login page
    def _root():
        return redirect(url_for("auth.login"))

    # --------------------- first-run bootstrap ---------------------------- #
    with app.app_context():
        db.create_all()

        # Ensure a default admin exists
        from ids.web.routes.auth import User  # local import to avoid cycles

        if not User.query.filter_by(username="admin").first():
            admin = User(username="admin", role="admin")
            admin.set_password("changeme")
            db.session.add(admin)
            db.session.commit()
            print("🛈 Created default admin (admin / changeme)")

    print(f"🛈 Web UI started in {env.upper()} mode — DB = {db_uri}")
    return app


# --------------------------------------------------------------------------- #
# CLI convenience                                                             #
# --------------------------------------------------------------------------- #
if __name__ == "__main__":  # Allow:  python -m ids.web.app
    create_app().run(debug=True)
