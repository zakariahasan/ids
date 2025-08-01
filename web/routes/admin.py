# ids/web/routes/admin.py
"""
Admin blueprint: create / delete users.

URL map
-------
/admin/                GET  → user-management page (admin.html)
/admin/add             POST → add a new user
/admin/delete/<id>     GET  → delete user by id
"""
from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ids.web.extensions import db
from ids.web.routes.auth import User, admin_required

bp = Blueprint("admin", __name__, url_prefix="/admin")


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #
def _render_user_mgmt():
    users = User.query.order_by(User.username).all()
    return render_template("admin.html", users=users, role="admin")


# --------------------------------------------------------------------------- #
# Routes                                                                       #
# --------------------------------------------------------------------------- #
@bp.route("/")
@admin_required
def user_mgmt():
    """Show user-management page with existing users."""
    return _render_user_mgmt()


@bp.route("/add", methods=["POST"])
@admin_required
def add_user():
    """Handle *Add User* form submission."""
    username = request.form["username"].strip()
    password = request.form["password"]
    role = request.form["role"]

    # Basic validation --------------------------------------------------
    if not username or not password or role not in ("admin", "user", "service account"):
        flash("Invalid input.", "error")
        return redirect(url_for("admin.user_mgmt"))

    if User.query.filter_by(username=username).first():
        flash("Username already exists.", "error")
        return redirect(url_for("admin.user_mgmt"))

    # Create user -------------------------------------------------------
    new_user = User(username=username, role=role)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    flash(f"User '{username}' added.", "success")
    return redirect(url_for("admin.user_mgmt"))


@bp.route("/delete/<int:user_id>")
@admin_required
def delete_user(user_id: int):
    """Delete a user by ID."""
    user = User.query.get_or_404(user_id)
    if user.username == "admin":
        flash("Cannot delete the default admin account.", "error")
    else:
        db.session.delete(user)
        db.session.commit()
        flash(f"User '{user.username}' deleted.", "success")
    return redirect(url_for("admin.user_mgmt"))
