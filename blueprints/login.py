"""Blueprint for login page."""

from flask import Blueprint


bp = Blueprint("login", __name__)


@bp.route("/register")
def register():
    """Register a user."""
    return "Register"

@bp.route("/login")
def login():
    """Log in a user."""
    return "Login"

@bp.route("/logout")
def logout():
    """Log out a user."""
    return "Logout"

