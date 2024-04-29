"""Blueprint for dashboard page."""

from pathlib import Path

from flask import Blueprint, render_template
from flask_login import login_required

from _types.forms import DownloadForm


this_filename = Path(__file__).name.split(".")[0]
bp = Blueprint(this_filename, __name__, url_prefix=f"/{this_filename}")



@bp.route("/dashboard")
@login_required
async def dashboard() -> str:
    """Dashboard page."""
    return render_template("dashboard.j2", form=DownloadForm())
