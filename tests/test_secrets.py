"""Secrets stay out of logs and Sentry, and stored Factorio tokens decrypt."""

import logging
from typing import TYPE_CHECKING, Any, cast

from hypothesis import given
from hypothesis import strategies as st

from api.logging_security import RedactingFilter, redact_text, scrub_event
from api.security import decrypt_factorio_token, encrypt_factorio_token
from tests.strategies import passwords

if TYPE_CHECKING:
    from sentry_sdk.types import Event

# Values as they appear in a query string or form body: no separators.
secret_values = st.from_regex(r"[A-Za-z0-9._~+/-]{8,40}", fullmatch=True)
keys = st.sampled_from(
    [
        "token",
        "password",
        "secret",
        "authorization",
        "factorio_token",
        "Token",
        "PASSWORD",
    ],
)


@given(token=st.text())
def test_factorio_token_round_trips(token: str) -> None:
    assert decrypt_factorio_token(encrypt_factorio_token(token)) == token


@given(token=secret_values)
def test_encrypted_token_does_not_contain_the_token(token: str) -> None:
    assert token.encode() not in encrypt_factorio_token(token)


@given(key=keys, value=secret_values, separator=st.sampled_from(["=", ": ", " = "]))
def test_redact_text_hides_the_value(key: str, value: str, separator: str) -> None:
    redacted = redact_text(f"GET /api/login?user=me&{key}{separator}{value}&page=2")

    assert value not in redacted
    assert f"{key}{separator}[REDACTED]" in redacted
    assert "user=me" in redacted
    assert "page=2" in redacted


@given(key=keys, value=secret_values)
def test_log_message_loses_its_secret(key: str, value: str) -> None:
    record = logging.LogRecord(
        "t",
        logging.INFO,
        __file__,
        1,
        f"login {key}={value}",
        None,
        None,
    )

    RedactingFilter().filter(record)

    assert value not in record.getMessage()


@given(password=passwords)
def test_log_args_lose_their_secrets(password: str) -> None:
    args = {"password": password, "user": "me"}
    record = logging.LogRecord(
        "t",
        logging.INFO,
        __file__,
        1,
        "%(user)s logs in with %(password)s",
        (args,),
        None,
    )

    RedactingFilter().filter(record)

    assert record.getMessage() == "me logs in with [REDACTED]"


def test_scrub_event_strips_cookies_and_auth_headers() -> None:
    # scrub_event edits the request in place, so the test keeps a reference.
    request: dict[str, Any] = {
        "cookies": {"fsm_session": "abc"},
        "headers": {"Authorization": "Bearer abc", "Accept": "text/html"},
        "query_string": "token=abc&page=2",
        "data": {"password": "abc", "nested": {"secret": "abc"}, "name": "server"},
    }
    event = cast("Event", {"request": request, "extra": {"factorio_token": "abc"}})

    scrubbed = scrub_event(event, {})

    assert scrubbed is not None
    assert "abc" not in repr(scrubbed)
    assert request["headers"]["Accept"] == "text/html"
    assert request["data"]["name"] == "server"
