"""Blueprint for login page."""

from pathlib import Path

from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import login_user, logout_user
from werkzeug import Response

from _types import FactorioInterface
from _types.database import User
from _types.forms import LoginForm


this_filename = Path(__file__).name.split(".")[0]
bp = Blueprint(this_filename, __name__, url_prefix=f"/{this_filename}")


@bp.route("/login", methods=["GET", "POST"])
async def login() -> str | Response:
    """Log in a user using their Factorio account."""
    # Required just a email and password, which get forwarded to the Factorio login page
    # Factorio login page will handle the rest and return oauth token which we use for
    # further requests like downloading mods etc.
    if request.method == "GET":
        return render_template("login.j2", form=LoginForm())
    if request.method == "POST":
        user = User.fetch_by_email(request.form["email"])
        fi = FactorioInterface()
        user.fi = fi

        login_user(user)

        return await user.fi.login_user(request.form["email"], request.form["password"])
    return redirect(request.referrer)


@bp.route("/logout")
def logout() -> Response:
    """Log out a user."""
    logout_user()
    return redirect(request.args.get("next") or request.referrer or url_for("/"))
