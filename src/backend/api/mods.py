"""Mod management API endpoints."""

import logging
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from backend.schemas import (
    ModBatchInstallRequest,
    ModEntry,
    ModInstallRequest,
    ModListResponse,
    ModSearchParams,
    ModToggleRequest,
)
from backend.security import CurrentUser
from FSM._types import FactorioInterface

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/search")
async def search_mods(
    query: str = "",
    page: int = 1,
    page_size: int = 12,
    server_name: str | None = None,
    current_user: CurrentUser = Depends(),
) -> dict[str, Any]:
    """Search for mods on Factorio mod portal."""
    fi = FactorioInterface()
    try:
        # Get server version if server_name provided
        factorio_version = None
        if server_name and server_name in current_user.servers:
            server = current_user.servers[server_name]
            factorio_version = server.version

        results = await fi.search_mods(
            query=query,
            page=page,
            page_size=page_size,
            factorio_version=factorio_version,
        )
        return results
    except Exception as e:
        logger.error(f"Mod search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search mods",
        ) from e
    finally:
        await fi.aio_http_session.close()


@router.get("/{mod_name}/details")
async def get_mod_details(mod_name: str) -> dict[str, Any]:
    """Get detailed information about a mod."""
    fi = FactorioInterface()
    try:
        details = await fi.get_mod_full(mod_name)
        return details
    except Exception as e:
        logger.error(f"Failed to get mod details for {mod_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mod '{mod_name}' not found",
        ) from e
    finally:
        await fi.aio_http_session.close()


@router.get("/{server_name}/mods", response_model=ModListResponse)
async def list_server_mods(server_name: str, current_user: CurrentUser) -> ModListResponse:
    """List all mods for a server."""
    if server_name not in current_user.servers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server '{server_name}' not found",
        )

    server = current_user.servers[server_name]
    mods = server.read_mod_list()

    return ModListResponse(
        mods=[
            ModEntry(
                name=mod["name"],
                enabled=mod["enabled"],
                version=mod.get("version"),
            )
            for mod in mods
        ]
    )


@router.post("/{server_name}/mods/install", status_code=status.HTTP_202_ACCEPTED)
async def install_mod(
    server_name: str,
    mod_data: ModInstallRequest,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    """Install a single mod on a server."""
    if server_name not in current_user.servers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server '{server_name}' not found",
        )

    server = current_user.servers[server_name]

    # Ensure user has Factorio token
    if not current_user.factorio_token or not current_user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Factorio credentials required for mod installation",
        )

    async def install_task() -> None:
        fi = FactorioInterface()
        try:
            # Get mod details
            mod_info = await fi.get_mod_full(mod_data.mod_name)

            # Find appropriate version
            releases = mod_info.get("releases", [])
            if not releases:
                raise ValueError(f"No releases found for mod {mod_data.mod_name}")

            # Use specified version or latest compatible
            target_release = None
            if mod_data.version:
                target_release = next(
                    (r for r in releases if r["version"] == mod_data.version),
                    None,
                )
            else:
                # Get latest release compatible with server version
                server_version = server.version
                target_release = releases[0]  # Latest by default
                if server_version:
                    compatible = [
                        r for r in releases
                        if r.get("info_json", {}).get("factorio_version", "0.0.0") <= server_version
                    ]
                    if compatible:
                        target_release = compatible[0]

            if not target_release:
                raise ValueError(f"No compatible version found for {mod_data.mod_name}")

            # Remove old versions
            server.remove_mod_archives(mod_data.mod_name)

            # Download mod
            download_url = target_release["download_url"]
            filename = target_release["file_name"]
            destination = server.mods / filename

            await fi.download_mod_release(
                download_url=download_url,
                destination=destination,
                username=current_user.email,
                token=current_user.factorio_token,
            )

            # Update mod list
            server.upsert_mod_entry(
                mod_data.mod_name,
                enabled=True,
                version=target_release["version"],
            )

            logger.info(f"Successfully installed mod {mod_data.mod_name} for server {server_name}")

        except Exception as e:
            logger.error(f"Failed to install mod {mod_data.mod_name}: {e}")
        finally:
            await fi.aio_http_session.close()

    background_tasks.add_task(install_task)

    return {"message": f"Installing mod {mod_data.mod_name}"}


@router.post("/{server_name}/mods/batch-install", status_code=status.HTTP_202_ACCEPTED)
async def batch_install_mods(
    server_name: str,
    batch_data: ModBatchInstallRequest,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    """Install multiple mods at once."""
    if server_name not in current_user.servers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server '{server_name}' not found",
        )

    server = current_user.servers[server_name]

    # Ensure user has Factorio token
    if not current_user.factorio_token or not current_user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Factorio credentials required for mod installation",
        )

    async def batch_install_task() -> None:
        fi = FactorioInterface()
        try:
            for mod_data in batch_data.mods:
                try:
                    # Get mod details
                    mod_info = await fi.get_mod_full(mod_data.mod_name)

                    # Find appropriate version
                    releases = mod_info.get("releases", [])
                    if not releases:
                        logger.warning(f"No releases found for mod {mod_data.mod_name}")
                        continue

                    # Use specified version or latest compatible
                    target_release = None
                    if mod_data.version:
                        target_release = next(
                            (r for r in releases if r["version"] == mod_data.version),
                            None,
                        )
                    else:
                        target_release = releases[0]

                    if not target_release:
                        logger.warning(f"No compatible version found for {mod_data.mod_name}")
                        continue

                    # Remove old versions
                    server.remove_mod_archives(mod_data.mod_name)

                    # Download mod
                    download_url = target_release["download_url"]
                    filename = target_release["file_name"]
                    destination = server.mods / filename

                    await fi.download_mod_release(
                        download_url=download_url,
                        destination=destination,
                        username=current_user.email,
                        token=current_user.factorio_token,
                    )

                    # Update mod list
                    server.upsert_mod_entry(
                        mod_data.mod_name,
                        enabled=True,
                        version=target_release["version"],
                    )

                    logger.info(f"Successfully installed mod {mod_data.mod_name}")

                except Exception as e:
                    logger.error(f"Failed to install mod {mod_data.mod_name}: {e}")
                    # Continue with other mods

        finally:
            await fi.aio_http_session.close()

    background_tasks.add_task(batch_install_task)

    return {"message": f"Installing {len(batch_data.mods)} mods"}


@router.patch("/{server_name}/mods/toggle", response_model=ModEntry)
async def toggle_mod(
    server_name: str,
    toggle_data: ModToggleRequest,
    current_user: CurrentUser,
) -> ModEntry:
    """Enable or disable a mod without uninstalling."""
    if server_name not in current_user.servers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server '{server_name}' not found",
        )

    server = current_user.servers[server_name]

    # Check if mod exists in mod list
    mods = server.read_mod_list()
    mod = next((m for m in mods if m["name"] == toggle_data.mod_name), None)

    if not mod:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mod '{toggle_data.mod_name}' not found in server mod list",
        )

    # Update mod state
    server.upsert_mod_entry(
        toggle_data.mod_name,
        enabled=toggle_data.enabled,
        version=mod.get("version"),
    )

    return ModEntry(
        name=toggle_data.mod_name,
        enabled=toggle_data.enabled,
        version=mod.get("version"),
    )


@router.delete("/{server_name}/mods/{mod_name}", status_code=status.HTTP_204_NO_CONTENT)
async def uninstall_mod(
    server_name: str,
    mod_name: str,
    current_user: CurrentUser,
) -> None:
    """Uninstall a mod from a server."""
    if server_name not in current_user.servers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server '{server_name}' not found",
        )

    if mod_name == "base":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot uninstall base mod",
        )

    server = current_user.servers[server_name]

    # Remove from mod list
    server.remove_mod_entry(mod_name)

    # Remove mod archives
    server.remove_mod_archives(mod_name)


@router.get("/{server_name}/mods/installed")
async def get_installed_mods(server_name: str, current_user: CurrentUser) -> dict[str, Any]:
    """Get installed mod archives with version information."""
    if server_name not in current_user.servers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server '{server_name}' not found",
        )

    server = current_user.servers[server_name]
    archives = server._discover_mod_archives()

    return {"installed_mods": archives}
