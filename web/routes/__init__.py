"""
ids.web.routes
==============

Aggregate and expose all blueprint objects for the web package.
"""

from __future__ import annotations

from flask import Flask

# Import individual blueprints
from .auth import bp as auth_bp
from .dashboard import bp as dashboard_bp
#from .train import bp as train_bp
from .home import bp as home_bp
from .admin import bp as admin_bp
from .alerts import bp as alerts_bp
from .train_supervised import bp as train_supervised_bp
from .train_unsupervised import bp as train_unsupervised_bp

__all__ = [
    "home_bp",
    "auth_bp",
    "dashboard_bp",
    "train_supervised_bp",
    "train_unsupervised_bp",
    "register_blueprints",
    "admin_bp",
    "alerts_bp",	
]

# Tuple of every blueprint (easy to iterate)
ALL_BLUEPRINTS = (
    home_bp, 
    auth_bp,
    dashboard_bp,
    train_supervised_bp,
    train_unsupervised_bp,
    admin_bp,
    alerts_bp, 
)


def register_blueprints(app: Flask) -> None:
    """
    Attach every blueprint in *ALL_BLUEPRINTS* to the given *app*.

    Usage
    -----
    >>> from ids.web.routes import register_blueprints
    >>> app = Flask(__name__)
    >>> register_blueprints(app)
    """
    for bp in ALL_BLUEPRINTS:
        app.register_blueprint(bp)
