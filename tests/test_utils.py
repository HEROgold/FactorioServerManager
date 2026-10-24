"""sanitize_str (user input to directory and container names), and the rate limiter."""

import uuid

from hypothesis import given
from hypothesis import strategies as st

from api.ratelimit import is_rate_limited
from api.utils import sanitize_str


@given(name=st.text())
def test_sanitized_name_has_no_path_or_shell_characters(name: str) -> None:
    sanitized = sanitize_str(name)

    assert all(c.isalnum() or c in "_-" for c in sanitized)
    assert not {"/", "\\", ".", " ", "$", ";"} & set(sanitized)


@given(name=st.text())
def test_sanitizing_twice_changes_nothing(name: str) -> None:
    assert sanitize_str(sanitize_str(name)) == sanitize_str(name)


@given(name=st.from_regex(r"[A-Za-z0-9_-]*", fullmatch=True))
def test_valid_names_pass_unchanged(name: str) -> None:
    assert sanitize_str(name) == name


@given(limit=st.integers(min_value=1, max_value=20))
def test_rate_limit_allows_exactly_limit_hits(limit: int) -> None:
    key = str(uuid.uuid4())

    allowed = [
        is_rate_limited(key, limit=limit, window_seconds=60, bucket="test")
        for _ in range(limit)
    ]

    assert not any(allowed)
    assert is_rate_limited(key, limit=limit, window_seconds=60, bucket="test")
