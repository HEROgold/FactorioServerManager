"""Hold random scripts for use in the project."""
from flask_login import login_required


@login_required
async def require_login() -> None:
    """Force use of login."""
    return
