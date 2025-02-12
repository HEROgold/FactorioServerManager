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
    dashboard_index = url_for("dashboard.index")
    if request.method == "GET":
        _next = request.args.get("next") or dashboard_index
        return render_template("login.j2", form=LoginForm(), next=_next)
    if request.method == "POST":
        _next = request.form.get("next") or dashboard_index
        user = User.fetch_by_email(request.form["email"])
        fi = FactorioInterface()
        user.fi = fi

        if resp := await user.fi.get_auth_token(request.form["email"], request.form["password"]):
            try:
                token = resp["token"]
            except KeyError:
                return "Login failed"
            if resp["email-authentication-required"] is not None:
                return "Email authentication required"
            user.factorio_token = token
            login_user(user)
            return redirect(_next)
        return "Login failed"
    return redirect(dashboard_index)


@bp.route("/logout")
def logout() -> Response:
    """Log out a user."""
    logout_user()
    return redirect(request.args.get("next") or request.referrer or url_for("/"))
