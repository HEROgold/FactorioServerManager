"""Blueprint for download page."""

from pathlib import Path
from typing import TYPE_CHECKING

from flask import Blueprint, redirect, render_template, request
from flask_login import (
    login_required,
)
from werkzeug import Response

from _types.forms import DownloadForm, InstallForm
from scripts import get_downloaded, get_installed
from scripts import install_server as inst_server


if TYPE_CHECKING:
    from _types.database import User
    from _types.dicts import Route


current_user: "User"

this_filename = Path(__file__).name.split(".")[0]
bp = Blueprint(this_filename, __name__, url_prefix=f"/{this_filename}")


@bp.before_request
@login_required
async def before_request() -> None:
    """Run before every request."""
    return


@bp.route("/")
@bp.route("/index")
async def index() -> str:
    """Dashboard page."""
    prefix = bp.url_prefix[1:] # type: ignore[reportOptionalSubscript]
    routes: list["Route"] = [
        {"name": "Download", "path": f"{prefix}.download"},
        {"name": "Server Overview", "path": f"{prefix}.server_overview"},
    ]
    return render_template("dashboard.j2", routes=routes, form=DownloadForm())


@bp.route("/download")
async def download() -> str:
    """Download page."""
    return render_template("download.j2", form=DownloadForm())


@bp.route("/server_overview")
async def server_overview() -> str:
    """Manage servers page."""
    downloaded = list(get_downloaded())
    installed = list(get_installed())
    return render_template("server_overview.j2", downloaded_servers=downloaded, installed_servers=installed)


@bp.route("/manage_server/<string:name>")
async def manage_server(name: str) -> str:
    """Manage a server page."""
    return render_template("manage_server.j2", server_name=name, form=InstallForm())


@bp.route("/install_server", methods=["POST"])
async def install_server() -> Response:
    """Manage a server page."""
    file = request.form["file"]
    port = int(request.form["port"])
    await inst_server(file, port)
    return redirect(request.referrer)
