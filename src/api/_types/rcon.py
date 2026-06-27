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


class RconError(Exception):
    """Raised when an RCON connection, authentication, or command fails."""


def _encode(req_id: int, req_type: int, body: str) -> bytes:
    payload = struct.pack("<ii", req_id, req_type) + body.encode("utf-8") + b"\x00\x00"
    return struct.pack("<i", len(payload)) + payload


async def _read_packet(reader: asyncio.StreamReader, timeout: float) -> tuple[int, int, str]:
    raw_len = await asyncio.wait_for(reader.readexactly(4), timeout)
    length = struct.unpack("<i", raw_len)[0]
    data = await asyncio.wait_for(reader.readexactly(length), timeout)
    req_id = struct.unpack("<i", data[0:4])[0]
    req_type = struct.unpack("<i", data[4:8])[0]
    body = data[8:-2].decode("utf-8", errors="replace")
    return req_id, req_type, body


async def execute(
    host: str,
    port: int,
    password: str,
    command: str,
    timeout: float = 5.0,
) -> str:
    """Authenticate and run a single RCON command, returning the response body."""
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout)
    except (OSError, TimeoutError) as err:
        msg = f"Unable to connect to RCON at {host}:{port}"
        raise RconError(msg) from err

    try:
        writer.write(_encode(1, _TYPE_AUTH, password))
        await writer.drain()

        auth_id, auth_type, _ = await _read_packet(reader, timeout)
        # Some servers emit an empty RESPONSE_VALUE before the auth response.
        if auth_type == _TYPE_RESPONSE:
            auth_id, _auth_type, _ = await _read_packet(reader, timeout)
        if auth_id == -1:
            msg = "RCON authentication failed (wrong password)"
            raise RconError(msg)

        writer.write(_encode(2, _TYPE_EXEC, command))
        await writer.drain()
        _, _, body = await _read_packet(reader, timeout)
        return body
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
