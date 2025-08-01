"""
ids.web
=======

Package entry-point that simply re-exports the ``create_app`` factory.

Example
-------
export FLASK_APP=ids.web:create_app
flask run
"""
from __future__ import annotations

# ONLY expose create_app – no direct blueprint imports here
from .app import create_app

__all__: list[str] = ["create_app"]