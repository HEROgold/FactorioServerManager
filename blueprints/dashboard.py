"""Blueprint for download page."""

from signal import SIGINT
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from flask import Blueprint, redirect, render_template, request
from flask_login import (
    login_required,
)
from werkzeug import Response

from _types.forms import DownloadForm, InstallForm, ManageServerForm
from config import SERVERS_DIRECTORY
from scripts import get_downloaded, get_installed
from scripts import install_server as inst_server
from scripts.server_settings import get_server_directories, get_server_settings


if TYPE_CHECKING:
    from _types.database import User
    from _types.dicts import Route


current_user: "User"
running_servers: dict[str, subprocess.Popen] = {}


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


# TODO: for first time launch, show all example settings and allow user to change them.
@bp.route("/manage_server/<string:name>/create", methods=["POST"])
async def create_server(name: str) -> Response:
    """Create a server."""
    server_directory = SERVERS_DIRECTORY/name
    executable, map_generation_settings, map_settings, server_settings = get_server_directories(name)

    subprocess.Popen(  # noqa: ASYNC101
        [  # noqa: S603
            str(executable),
            f"--create {server_directory}"
            f"--map-gen-settings {map_generation_settings}"
            f"--map-settings {map_settings}"
            f"--server-settings {server_settings}"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    ).wait()
    return redirect(request.referrer)


# TODO: Track running servers and their processes and process ids
# TODO: Add separate saves for each server.
@bp.route("/manage_server/<string:name>/start", methods=["POST"])
async def start_server(name: str) -> Response:
    """Start a server."""
    server_directory = SERVERS_DIRECTORY/name
    executable, map_generation_settings, map_settings, server_settings = get_server_directories(name)

    with (
        Path(server_directory/"stdout.txt").open("w") as stdout_file,  # noqa: ASYNC101
        Path(server_directory/"stderr.txt").open("w") as stderr_file  # noqa: ASYNC101
    ):
        p = subprocess.Popen(  # noqa: ASYNC101
            [  # noqa: S603
                str(executable),
                f"--map-gen-settings {map_generation_settings}"
                f"--map-settings {map_settings}"
                f"--server-settings {server_settings}"
            ],
            stdout=stdout_file,
            stderr=stderr_file
        )
        running_servers[name] = p

    return redirect(request.referrer)


@bp.route("/manage_server/<string:name>/stop", methods=["POST"])
async def stop_server(name: str) -> Response:
    """Stop a server."""
    process = running_servers[name]
    process.communicate("/server-save\n", timeout=120) # 2 minute generous timeout
    process.send_signal(SIGINT)
    return redirect(request.referrer)


@bp.route("/manage_server/<string:name>/restart", methods=["POST"])
async def restart_server(name: str) -> Response:
    """Restart a server."""
    await stop_server(name)
    await start_server(name)
    return redirect(request.referrer)
