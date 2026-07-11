"""Shared utility helpers for the fsm API."""


def sanitize_str(name: str) -> str:
    """Sanitize the string. Keeps only 0-9, a-z, A-Z, ``_`` and ``-``.

    Hyphens are preserved (they are valid in directory and Docker container
    names) so a name like ``test-server`` is not silently collapsed to
    ``testserver``.
    """
    return "".join([c for c in name if c.isalnum() or c in "_-"])
