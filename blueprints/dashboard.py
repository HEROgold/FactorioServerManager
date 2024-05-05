"""Blueprint for dashboard page."""

from pathlib import Path
from typing import TYPE_CHECKING

from flask import Blueprint, render_template
from flask_login import (
    current_user,  # type: ignore[ReportAssignmentType]
    login_required
)

from _types.forms import DownloadForm

if TYPE_CHECKING:
    from _types.database import User


current_user: "User"

this_filename = Path(__file__).name.split(".")[0]
bp = Blueprint(this_filename, __name__, url_prefix=f"/{this_filename}")

@bp.before_request
@login_required
def before_request() -> None:
    """Run before every request."""
    return


# TODO: rename dashboard for this function to download (shows download page)
@bp.route("/dashboard")
async def dashboard() -> str:
    """Dashboard page."""
    return render_template("dashboard.j2", form=DownloadForm())


# TODO: Add template
@bp.route("/server_overview")
async def server_overview() -> str:
    """Manage servers page."""
    servers = [
        server
        async for server in current_user.fi.get_downloaded()
    ]
    return render_template("server_overview.j2", servers=servers)



# TODO: Add template
@bp.route("/manage_server/<int:server_id>")
async def manage_server(server_id: int) -> str:
    """Manage a server page."""
    return render_template("manage_server.j2", server_id=server_id)
