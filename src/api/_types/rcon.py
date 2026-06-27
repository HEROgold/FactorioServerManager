"""Minimal asyncio Source RCON client.

Factorio's headless server speaks the Source RCON protocol. Rather than add a
third-party dependency we implement the tiny slice we need: authenticate, run a
single command, return the response body.
"""

from __future__ import annotations

import asyncio
import contextlib
import struct

# Source RCON packet types.
_TYPE_AUTH = 3
_TYPE_AUTH_RESPONSE = 2
_TYPE_EXEC = 2
_TYPE_RESPONSE = 0

# Request ids we assign so we can correlate replies.
_ID_AUTH = 1
_ID_EXEC = 2
_ID_SENTINEL = 3


class RconError(Exception):
    """Raised when an RCON connection, authentication, or command fails."""


def _encode(req_id: int, req_type: int, body: str) -> bytes:
    payload = struct.pack("<ii", req_id, req_type) + body.encode("utf-8") + b"\x00\x00"
    return struct.pack("<i", len(payload)) + payload


async def _read_packet(reader: asyncio.StreamReader) -> tuple[int, int, str]:
    raw_len = await reader.readexactly(4)
    length = struct.unpack("<i", raw_len)[0]
    data = await reader.readexactly(length)
    req_id = struct.unpack("<i", data[0:4])[0]
    req_type = struct.unpack("<i", data[4:8])[0]
    body = data[8:-2].decode("utf-8", errors="replace")
    return req_id, req_type, body


async def execute(
    host: str,
    port: int,
    password: str,
    command: str,
) -> str:
    """Authenticate and run a single RCON command, returning the response body."""
    try:
        reader, writer = await asyncio.open_connection(host, port)
    except (OSError, TimeoutError) as err:
        msg = f"Unable to connect to RCON at {host}:{port}"
        raise RconError(msg) from err

    try:
        writer.write(_encode(_ID_AUTH, _TYPE_AUTH, password))
        await writer.drain()

        auth_id, auth_type, _ = await _read_packet(reader)
        # Some servers emit an empty RESPONSE_VALUE before the auth response.
        if auth_type == _TYPE_RESPONSE:
            auth_id, _auth_type, _ = await _read_packet(reader)
        if auth_id == -1:
            msg = "RCON authentication failed (wrong password)"
            raise RconError(msg)

        # Send the command, then a sentinel empty RESPONSE_VALUE. A Factorio
        # reply can span multiple RESPONSE_VALUE packets; the server processes
        # requests in order, so once we see the sentinel's id echoed back we
        # know every command-response packet has arrived.
        writer.write(_encode(_ID_EXEC, _TYPE_EXEC, command))
        writer.write(_encode(_ID_SENTINEL, _TYPE_RESPONSE, ""))
        await writer.drain()

        parts: list[str] = []
        while True:
            resp_id, _resp_type, body = await _read_packet(reader)
            if resp_id == _ID_SENTINEL:
                break
            if resp_id == _ID_EXEC:
                parts.append(body)
        return "".join(parts)
    except TimeoutError as err:
        msg = "RCON command timed out"
        raise RconError(msg) from err
    except asyncio.IncompleteReadError as err:
        msg = "RCON connection closed unexpectedly"
        raise RconError(msg) from err
    finally:
        writer.close()
        with contextlib.suppress(Exception):
            await writer.wait_closed()
