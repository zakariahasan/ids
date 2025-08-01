"""Landing / home page blueprint."""
from __future__ import annotations

from flask import Blueprint, render_template, g, redirect, url_for

bp = Blueprint("home", __name__)  # no url_prefix so '/' is the root


@bp.route("/")
def index():
    # If the user isn't logged in, bounce them to login first
    if g.get("user") is None:
        return redirect(url_for("auth.login"))

    # Pass username / role into your template
    return render_template(
        "index.html",
        username=g.user.username,  # type: ignore[attr-defined]
        role=g.user.role,          # type: ignore[attr-defined]
    )
