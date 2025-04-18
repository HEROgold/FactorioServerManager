"""String utilities."""

def sanitize(name: str) -> str:
    """Sanitize the string. Makes sure it only contains 0-9, a-z, A-Z, and _."""
    return "".join([c for c in name if c.isalnum() or c == "_"])
