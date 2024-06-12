"""Blueprint for download page."""

from pathlib import Path
from typing import TYPE_CHECKING

import docker
from flask import Blueprint, redirect, render_template, request
from flask_login import (
    current_user,  # type: ignore[reportAssignmentType]
    login_required,
)
from werkzeug import Response

from _types.data import Server
from _types.forms import DownloadForm, InstallForm, ManageServerForm
from config import DOCKER_CONTAINER_PREFIX
from scripts import get_downloaded, get_installed
from scripts import install_server as inst_server


if TYPE_CHECKING:
    from _types.database import User
    from _types.dicts import Route
    current_user: "User"



docker_client = docker.from_env()

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
    server = Server(name)

    for key, value in server.settings.__dataclass_fields__.items():
        current_settings[key] = value

    form = ManageServerForm(**current_settings)
    return render_template("manage_server.j2", name=name, form=form)


@bp.route("/manage_server/<string:name>/create", methods=["POST"])
async def create_server(name: str) -> Response:
    """Create a server."""
    server = Server(name)
    docker_client.containers.create(
        image="factoriotools/factorio",
        detach=True,
        ports={"34197/udp": 34197, "27015/tcp": 27015},
        volumes=[
            f"{server.server_directory}:/factorio",
        ],
        name=f"{DOCKER_CONTAINER_PREFIX}{server.name}",
        restart_policy={"Name": "on-failure", "MaximumRetryCount": 2},
    )
    # TODO: redirect to server overview page, which allows settings to be changed, before first start.
    return redirect(request.referrer)


@bp.route("/manage_server/<string:name>/start", methods=["POST"])
async def start_server(name: str) -> Response:
    """Start a server through a http request."""
    # TODO: show server logs
    await _start_server(name)
    return redirect(request.referrer)

@bp.route("/manage_server/<string:name>/stop", methods=["POST"])
async def stop_server(name: str) -> Response:
    """Stop a server through a http request."""
    await _stop_server(name)
    return redirect(request.referrer)


@bp.route("/manage_server/<string:name>/restart", methods=["POST"])
async def restart_server(name: str) -> Response:
    """Restart a server through a http request."""
    await _restart_server(name)
    return redirect(request.referrer)


async def _start_server(name: str) -> None:
    server = Server(name, current_user)
    docker_client.containers.run(
        image="factoriotools/factorio",
        detach=True,
        ports={"34197/udp": 34197, "27015/tcp": 27015},
        volumes=[
            f"{server.server_directory}:/factorio",
        ],
        name=f"{DOCKER_CONTAINER_PREFIX}{server.name}",
        restart_policy={"Name": "on-failure", "MaximumRetryCount": 2},
    )


async def _stop_server(name: str) -> None:
    server = Server(name)
    docker_client.containers.get(f"{DOCKER_CONTAINER_PREFIX}{server.name}").stop()


async def _restart_server(name: str) -> None:
    await _stop_server(name)
    await _start_server(name)

