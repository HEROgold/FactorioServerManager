"""Blueprint for login page."""

from pathlib import Path

from flask import Blueprint


this_filename = Path(__file__).name.split(".")[0]
bp = Blueprint(this_filename, __name__, url_prefix=f"/{this_filename}")


@bp.route("/register")
def register() -> str:
    """Register a user."""
    return "Register"


@bp.route("/delete")
def delete() -> str:
    """Delete a user's account."""
    return "Delete Account"


@bp.route("/login")
def login() -> str:
    """Log in a user."""
    return "Login"


@bp.route("/logout")
def logout() -> str:
    """Log out a user."""
    return "Logout"


@bp.route("/factorio_login")
def factorio_login() -> str:
    """Log in a user using their Factorio account."""
    # Required just a email and password, which get forwarded to the Factorio login page
    # Factorio login page will handle the rest and return oauth token which we use for
    # further requests like downloading mods etc.
    return "Factorio Login"


@bp.route("/factorio_logout")
def factorio_logout() -> str:
    """Log out a user from their Factorio account."""
    return "Factorio Logout"
