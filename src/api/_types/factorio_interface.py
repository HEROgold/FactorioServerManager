import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Self, TypedDict

from bs4 import BeautifulSoup, Tag
from herogold.log import LoggerMixin

from api.config import Config
from api.constants import (
    API_VERSION,
    LOGIN_API,
    LOGIN_URL,
    MODS_API_URL,
    AppConfig,
)

if TYPE_CHECKING:
    from datetime import datetime

    import httpxyz
    from httpxyz import AsyncClient

MOD_PORTAL_BASE = "https://mods.factorio.com"

# A sanity cap on a single mod archive download; mod zips are a few MB to tens
# of MB, so anything past this is either a bug or an attempt to fill the disk.
MAX_BYTES = 500 * 1024 * 1024

_SEARCH_FIELDS = ("name", "title", "summary", "owner")

# Factorio mod portal names are restricted to this charset; anything else
# could break out of the URL path segment below (e.g. "../", "://") and
# redirect the request to an attacker-controlled host (SSRF).
_MOD_NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def _validate_mod_name(mod_name: str) -> str:
    if not _MOD_NAME_RE.match(mod_name):
        msg = f"Invalid mod name: {mod_name!r}"
        raise ValueError(msg)
    return mod_name


def _search_haystack(mod: dict) -> str:
    """Build a lowercase searchable string from a mod's text fields."""
    return " ".join(str(mod.get(field) or "") for field in _SEARCH_FIELDS).casefold()

@dataclass
class CSRFToken:
    token: str

@dataclass
class AuthToken:
    username: str
    token: str | None = None
    email_authentication_required: bool | None = None

@dataclass
class ModSearch:
    name: str
    title: str
    summary: str

class ModLicense(TypedDict):
    description: str
    id: str
    name: str
    title: str
    url: str

class ModInfoJson(TypedDict):
    dependencies: list[str]
    factorio_version: str

class ModRelease(TypedDict):
    download_url: str  # Url to download the mod release
    file_name: str
    info_json: ModInfoJson
    released_at: datetime
    sha1: str
    version: str

class Mod(TypedDict):
    """Represents a Factorio mod with its metadata and download information."""

    category: str
    changelog: str
    created_at: datetime
    homepage: str | None
    images: list[str]
    license: ModLicense
    downloads_count: int
    description: str
    name: str
    owner: str  # UserName (same as login username.)
    releases: list[ModRelease]
    score: float
    summary: str
    tags: list[str]
    thumbnail: str  # Url to the thumbnail image.
    title: str
    updated_at: datetime

class ModsInterface(LoggerMixin):
    """Interface for interacting with the Factorio mod portal.

    including searching for mods and downloading them.
    """

    client: httpxyz.AsyncClient
    base_url = Config("https://mods.factorio.com")

    # The full mod list barely changes minute-to-minute but is ~megabytes and
    # shared by every user/search, so it's cached process-wide rather than
    # refetched on every keystroke -- both for latency and to stay well clear
    # of the portal's rate limits. Keyed by the `factorio_version` filter since
    # that changes what the portal returns. Per-mod detail (thumbnails,
    # releases) is cached the same way, keyed by mod name.
    _LIST_CACHE_TTL_SECONDS = 300
    _DETAIL_CACHE_TTL_SECONDS = 300

    def __init__(self, client: httpxyz.AsyncClient) -> None:
        self.client = client
        self._list_cache: dict[str | None, tuple[float, dict]] = {}
        self._detail_cache: dict[str, tuple[float, Mod]] = {}

    async def _fetch_mod_list(self: Self, factorio_version: str | None) -> dict:
        cached = self._list_cache.get(factorio_version)
        if cached and time.monotonic() - cached[0] < self._LIST_CACHE_TTL_SECONDS:
            return cached[1]

        params: dict[str, str | int] = {"page_size": "max"}
        if factorio_version:
            params["version"] = factorio_version
        # The full list is large, so allow more time than the default client timeout.
        resp = await self.client.get(MODS_API_URL, params=params, timeout=30.0)
        resp.raise_for_status()
        payload = resp.json()
        self._list_cache[factorio_version] = (time.monotonic(), payload)
        return payload

    async def search(
        self: Self,
        *,
        query: str = "",
        page: int = 1,
        page_size: int = 12,
        factorio_version: str | None = None,
    ) -> dict:
        """Search the mod portal.

        The current mod portal API (Factorio 2.x) no longer supports server-side
        text search: ``/api/mods`` ignores the legacy ``q`` parameter and always
        returns the full list. We therefore fetch the full list once (cached,
        see ``_fetch_mod_list``) and filter client-side by
        name/title/summary/owner, then paginate locally.
        """
        payload = await self._fetch_mod_list(factorio_version)
        results: list[dict] = payload.get("results", []) if isinstance(payload, dict) else []
        if query:
            needle = query.casefold()
            results = [mod for mod in results if needle in _search_haystack(mod)]

        total = len(results)
        page_count = max((total + page_size - 1) // page_size, 1)
        page = min(max(page, 1), page_count)
        start = (page - 1) * page_size
        return {
            "results": results[start:start + page_size],
            "pagination": {
                "count": total,
                "page": page,
                "page_count": page_count,
                "page_size": page_size,
            },
        }

    async def get(self: Self, mod_name: str) -> Mod:
        """Get the full details for a mod by its name (cached, see class docstring)."""
        cached = self._detail_cache.get(mod_name)
        if cached and time.monotonic() - cached[0] < self._DETAIL_CACHE_TTL_SECONDS:
            return cached[1]

        url = f"{MODS_API_URL}/{_validate_mod_name(mod_name)}/full"
        resp = await self.client.get(url)  # skylos: ignore -- mod_name is charset-validated above
        resp.raise_for_status()
        mod: Mod = resp.json()
        self._detail_cache[mod_name] = (time.monotonic(), mod)
        return mod

    async def download(
        self: Self,
        mod: Mod,
        username: str,
        token: str,
    ) -> Path:
        """Download the latest release of a mod."""
        if not mod["releases"]:
            msg = f"Mod {mod['name']} has no releases to download"
            raise ValueError(msg)
        latest_release = mod["releases"][0]
        url = latest_release["download_url"]
        destination = Path("downloads") / mod["name"] / latest_release["file_name"]
        return await self.download_release(
            download_url=url,
            destination=destination,
            username=username,
            token=token,
        )

    async def download_release(
        self: Self,
        *,
        download_url: str,
        destination: Path,
        username: str,
        token: str,
    ) -> Path:
        if not username or not token:
            msg = "Factorio credentials required for mod downloads"
            raise ValueError(msg)
        url = download_url
        if not download_url.startswith("http"):
            url = f"{MOD_PORTAL_BASE}{download_url}"
        params = {"username": username, "token": token}
        destination.parent.mkdir(parents=True, exist_ok=True)
        # Stream to a temporary sibling and atomically swap it into place so a
        # crash mid-download can never leave a truncated zip in the shared store.
        partial = destination.with_name(destination.name + ".part")
        if destination.is_symlink() or partial.is_symlink():
            msg = f"Refusing to download mod archive over a symlink: {destination}"
            raise ValueError(msg)
        try:
            written = 0
            async with self.client.stream("GET", url, params=params, timeout=120.0) as resp:
                resp.raise_for_status()
                with partial.open("wb") as f:  # skylos: ignore -- symlink-checked above; size-capped below
                    async for chunk in resp.aiter_bytes(32768):
                        written += len(chunk)
                        if written > MAX_BYTES:
                            msg = f"Mod archive exceeded the {MAX_BYTES}-byte download cap"
                            raise ValueError(msg)
                        f.write(chunk)
            partial.replace(destination)
        except BaseException:
            partial.unlink(missing_ok=True)
            raise
        return destination

class FactorioInterface(LoggerMixin):
    client: httpxyz.AsyncClient
    mods: ModsInterface

    def __init__(self, client: AsyncClient, mods: ModsInterface) -> None:
        self.client = client
        self.mods = mods

    async def aclose(self: Self) -> None:
        """Close the underlying HTTP client."""
        await self.client.aclose()

    async def _get_csrf_details(self: Self) -> CSRFToken:
        """Get the csrf token from the login page."""
        resp = await self.client.get(LOGIN_URL)
        soup = BeautifulSoup(resp.text, "html.parser")
        tag = soup.find("input", {"name": "csrf_token"})
        if isinstance(tag, Tag):
            value = tag.get("value")
            if isinstance(value, str):
                return CSRFToken(token=value)

        msg = "Could not find csrf token"
        raise ValueError(msg)

    async def get_auth_token(
        self: Self,
        username_or_email: str,
        password: str,
        email_authentication_code: str | None = None,
    ) -> AuthToken:
        """Log in the user with the given username and password, and optionally an email code.

        Parameters
        ----------
        username_or_email: :class:`str`
            the username or the email for the login
        password: :class:`str`
            the password for logging in
        email_authentication_code: :class:`str`
            the email authentication code that might be required for logging in

        """
        data: dict[str, str] = {
            "username": username_or_email,
            "password": password,
            "api_version": str(API_VERSION),
        }
        if AppConfig.REQUIRE_GAME_OWNERSHIP:
            data["require_game_ownership"] = "true"
        if email_authentication_code:
            data["email_authentication_code"] = email_authentication_code

        resp = await self.client.post(LOGIN_API, data=data)
        payload = resp.json()

        # api_version <= 1 returns a bare list of token strings.
        if isinstance(payload, list):
            token = payload[0] if payload else None
            return AuthToken(username=username_or_email, token=token)

        # api_version >= 2 returns an object: {token, username} on success, or
        # an error object {error, message} (e.g. "email-authentication-required").
        if isinstance(payload, dict):
            if payload.get("error") == "email-authentication-required":
                return AuthToken(
                    username=username_or_email,
                    email_authentication_required=True,
                )
            return AuthToken(
                username=payload.get("username", username_or_email),
                token=payload.get("token"),
            )

        return AuthToken(username=username_or_email)
