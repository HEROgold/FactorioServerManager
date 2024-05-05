"""Blueprint for download page."""

from pathlib import Path
from typing import TYPE_CHECKING

from flask import Blueprint, redirect, render_template, request
from flask_login import (
    login_required,
)
from werkzeug import Response

from _types.forms import DownloadForm, InstallForm, ManageServerForm
from scripts import get_downloaded, get_installed
from scripts import install_server as inst_server
from scripts.server_settings import get_server_settings


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


@bp.route("/install_server/<string:name>", methods=["GET", "POST"])
async def install_server(name: str) -> Response | str:
    """Manage a server page."""
    if request.method == "GET":
        installed = [
            i
            for i in get_installed()
            if i.name == name
        ]
        return render_template(
            "install_server.j2",
            form=InstallForm(),
            server_name=name,
            installed_servers=installed
        )
    if request.method == "POST":
        file = request.form["file"]
        name = request.form["name"]
        port = int(request.form["port"])
        await inst_server(name, file, port)
        return redirect(request.referrer)
    return redirect(request.referrer, code=400)


@bp.route("/server_overview")
async def server_overview() -> str:
    """Manage servers page."""
    downloaded = list(get_downloaded())
    installed = list(get_installed())
    return render_template("server_overview.j2", downloaded_servers=downloaded, installed_servers=installed)


@bp.route("/manage_server/<string:name>")
async def manage_server(name: str) -> str:
    """Manage a server page."""
    current_settings: dict[str, str] = {}

    async for key, value in get_server_settings(name):
        current_settings[key] = value

    form = ManageServerForm(**current_settings)
    return render_template("manage_server.j2", name=name, form=form)


# TODO: Track running servers and their processes and process ids
@bp.route("/manage_server/<string:name>/start", methods=["POST"])
async def start_server(name: str) -> Response:
    """Start a server."""
    return redirect(request.referrer)


@bp.route("/manage_server/<string:name>/stop", methods=["POST"])
async def stop_server(name: str) -> Response:
    """Stop a server."""
    return redirect(request.referrer)


@bp.route("/manage_server/<string:name>/restart", methods=["POST"])
async def restart_server(name: str) -> Response:
    """Restart a server."""
    await stop_server(name)
    await start_server(name)
    return redirect(request.referrer)
