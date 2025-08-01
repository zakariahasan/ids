"""
Authentication blueprint – now uses the global `db` extension instead of
touching `current_app` at import time.
"""
from __future__ import annotations

from functools import wraps

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from ids.web.extensions import db           # <<< NEW – no current_app here

bp = Blueprint("auth", __name__, url_prefix="/auth")

# --------------------------------------------------------------------------- #
# User model                                                                   #
# --------------------------------------------------------------------------- #
class User(db.Model):                       # type: ignore[misc]
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(16), default="user")  # 'admin' or 'user'

    # helpers
    def set_password(self, password: str) -> None:
        self.password = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password, password)

# --------------------------------------------------------------------------- #
# Blueprint hooks & decorators                                                 #
# --------------------------------------------------------------------------- #

@bp.before_app_request
def _load_logged_in_user() -> None:
    user_id = session.get("user_id")
    g.user = User.query.get(user_id) if user_id else None

def login_required(view):                   # type: ignore[override]
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.get("user") is None:
            flash("Please log in to access this page.", "error")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped

def admin_required(view):                   # type: ignore[override]
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.get("user") is None or g.user.role != "admin":  # type: ignore[attr-defined]
            flash("Admin privileges required.", "error")
            return redirect(url_for("dashboard.view"))
        return view(*args, **kwargs)
    return wrapped

# --------------------------------------------------------------------------- #
# Routes                                                                       #
# --------------------------------------------------------------------------- #
@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"].strip()).first()
        if user and user.check_password(request.form["password"].strip()):
            session.clear()
            session["user_id"] = user.id
            session["role"] = user.role
            flash("Logged in.", "success")
            return redirect(url_for("dashboard.view"))
        flash("Invalid credentials.", "error")
    return render_template("login.html")

@bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
