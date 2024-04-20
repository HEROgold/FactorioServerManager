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

@bp.route("/factorio_login")
def factorio_login():
    """Log in a user using their Factorio account."""
    # Required just a email and password, which get forwarded to the Factorio login page
    return "Factorio Login"
