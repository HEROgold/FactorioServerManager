"""Blueprint for manipulating files."""

from pathlib import Path

from flask import Blueprint, redirect, url_for
from flask_login import UserMixin, current_user  # type: ignore[ReportAssignmentType]
from werkzeug import Response


current_user: UserMixin

this_filename = Path(__file__).name.split(".")[0]
bp = Blueprint(this_filename, __name__, url_prefix=f"/{this_filename}")


@bp.before_request
def before_request() -> None | Response:
    """Run before every request."""
    if current_user.is_authenticated:
        return None
    return redirect(url_for("login.login"))


@bp.route("/get_all", methods=["GET"])
def get_all():
    """Get all files."""
    return list(Path().rglob("*"))


@bp.route("/get", methods=["GET"])
def get() -> str:
    """Get a file."""
    return "Get a file"


@bp.route("/create", methods=["POST"])
def create() -> str:
    """Create a file."""
    return "Create a file"


@bp.route("/update", methods=["PUT"])
def update() -> str:
    """Update a file."""
    return "Update a file"


@bp.route("/delete", methods=["DELETE"])
def delete() -> str:
    """Delete a file."""
    return "Delete a file"
