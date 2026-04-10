from pathlib import Path
from typing import TYPE_CHECKING, Self

import aiohttp
from bs4 import BeautifulSoup
from herogold.log import LoggerMixin
from pydantic.dataclasses import dataclass
from sqlalchemy.util.typing import TypedDict

from api.config import Config
from fsm.config import (
    API_VERSION,
    LOGIN_API,
    LOGIN_URL,
    MODS_API_URL,
    AppConfig,
    HTTPConfig,
)

if TYPE_CHECKING:
    from datetime import datetime

MOD_PORTAL_BASE = "https://mods.factorio.com"

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

    aio_http_session: aiohttp.ClientSession
    base_url = Config("https://mods.factorio.com")

    def __init__(self, aiohttp: aiohttp.ClientSession) -> None:
        self.aio_http_session = aiohttp

    async def search(
        self: Self,
        *,
        query: str = "",
        page: int = 1,
        page_size: int = 12,
        factorio_version: str | None = None,
    ) -> list[ModSearch]:
        params = {"page": page, "page_size": page_size}
        if query:
            params["q"] = query
        if factorio_version:
            params["version"] = factorio_version
        async with self.aio_http_session.get(MODS_API_URL, params=params) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get(self: Self, mod_name: str) -> Mod:
        """Get the full details for a mod by its name."""
        url = f"{MODS_API_URL}/{mod_name}/full"
        async with self.aio_http_session.get(url) as resp:
            resp.raise_for_status()
            return await resp.json()

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
        async with self.aio_http_session.get(url, params=params) as resp:
            resp.raise_for_status()
            with destination.open("wb") as f:
                async for chunk in resp.content.iter_chunked(32768):
                    f.write(chunk)
        return destination

class FactorioInterface(LoggerMixin):
    aio_http_session: aiohttp.ClientSession
    mods: ModsInterface

    def __init__(self) -> None:
        self.aio_http_session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=HTTPConfig.timeout))
        self.mods = ModsInterface(self.aio_http_session)

    async def _get_csrf_details(self: Self) -> CSRFToken:
        """Get the csrf token from the login page."""
        async with self.aio_http_session.get(LOGIN_URL) as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, "html.parser")
            if tag := soup.find("input", {"name": "csrf_token"}):
                return CSRFToken(token=tag.get("value"))

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
        data = {
            "username": username_or_email,
            "password": password,
            "api_version": API_VERSION,
            "require_game_ownership": AppConfig.REQUIRE_GAME_OWNERSHIP,
            "email_authentication_code": email_authentication_code,
        }
        async with self.aio_http_session.post(LOGIN_API, data=data) as resp:
            return AuthToken(**await resp.json())
