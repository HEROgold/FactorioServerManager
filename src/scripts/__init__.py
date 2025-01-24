"""Hold random scripts for use in the project."""
from flask_login import login_required


@login_required
async def require_login() -> None:
    """Force use of login."""
    return


def sanitize_str(name: str) -> str:
    """Sanitize the string. Makes sure it only contains 0-9, a-z, A-Z, and _."""
    return "".join([c for c in name if c.isalnum() or c == "_"])
