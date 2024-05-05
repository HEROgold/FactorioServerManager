"""Blueprint for manipulating files."""

from pathlib import Path
from typing import TYPE_CHECKING

from flask import Blueprint, redirect, request, url_for
from flask_login import current_user  # type: ignore[ReportAssignmentType]
from werkzeug import Response

from _types.enums import Build, Distro
from config import DOWNLOADS_DIRECTORY


if TYPE_CHECKING:
    from _types.database import User


current_user: "User"

this_filename = Path(__file__).name.split(".")[0]
bp = Blueprint(this_filename, __name__, url_prefix=f"/{this_filename}")


@bp.before_request
def before_request() -> None | Response:
    """Run before every request."""
    if current_user.is_authenticated:
        return None
    return redirect(url_for("login.login"))


@bp.route("/get_all", methods=["GET"])
def get_all() -> list[Path]:
    """Get all files."""
    return list(Path(DOWNLOADS_DIRECTORY).rglob("*"))


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


@bp.route("/download_server", methods=["GET", "POST"])
async def download_server() -> Response:
    """Download a file."""
    if (
        (build := request.form["build"]) and
        (distro := request.form["distro"]) and
        (version := request.form["version"])
        or
        (build := request.args.get("build")) and
        (distro := request.args.get("distro")) and
        (version := request.args.get("version"))
    ):
        # TODO: run download in another thread or subprocess or something to not block the server.
        await current_user.fi.download_server_files(Build[build], Distro[distro], version)
        return redirect(url_for("dashboard.server_overview"))
    return redirect(request.referrer, code=400)
