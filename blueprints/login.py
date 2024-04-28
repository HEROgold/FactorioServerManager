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


@bp.route("/register")
def register() -> str:
    """Register a user."""
    return "Register"


@bp.route("/delete")
def delete() -> str:
    """Delete a user's account."""
    return "Delete Account"


@bp.route("/login")
def login() -> str | Response:
    """Log in a user."""
    if request.method == "GET":
        form = LoginForm()
        if form.validate_on_submit():
            login_user(User.fetch_by_email(form.email.data)) # type: ignore[ReportArgumentType]
        return render_template("factorio_login.j2", form=form)

    if request.method == "POST":
        login_user(User.fetch_by_email(request.form["email"]))
        return render_template("factorio_login.j2")

    return redirect(url_for("/"))


@bp.route("/logout")
def logout() -> Response:
    """Log out a user."""
    logout_user()
    return redirect(request.referrer)


@bp.route("/factorio_login", methods=["GET", "POST"])
async def factorio_login() -> str | Response:
    """Log in a user using their Factorio account."""
    # Required just a email and password, which get forwarded to the Factorio login page
    # Factorio login page will handle the rest and return oauth token which we use for
    # further requests like downloading mods etc.
    if request.method == "GET":
        return render_template("factorio_login.j2", form=LoginForm())
    if request.method == "POST":
        fi = FactorioInterface()
        user = User.fetch_by_email(request.form["email"])
        user.fi = fi

        return await user.fi.login_user(request.form["email"], request.form["password"])
    return redirect(request.referrer)


@bp.route("/factorio_logout")
def factorio_logout() -> str:
    """Log out a user from their Factorio account."""
    return "Factorio Logout"


@bp.route("/profile")
def profile() -> str:
    """Profile page."""
    return render_template("profile.j2")
