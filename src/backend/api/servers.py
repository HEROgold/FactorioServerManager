"""Server management API endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from backend.rate_limit import require_operation_cooldown, set_operation_cooldown
from backend.schemas import ServerCreate, ServerInfo, ServerStatus, ServerUpdate
from backend.security import CurrentUser
from FSM._types.data import Server

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=list[ServerInfo])
async def list_servers(current_user: CurrentUser) -> list[ServerInfo]:
    """List all servers for the current user."""
    servers = []
    for name, server in current_user.servers.items():
        servers.append(
            ServerInfo(
                name=name,
                status=server.status.value,
                version=server.version,
                port=server.port if server.version else None,
                ip=server.ip if server.version else None,
            )
        )
    return servers


@router.get("/{server_name}", response_model=ServerInfo)
async def get_server(server_name: str, current_user: CurrentUser) -> ServerInfo:
    """Get information about a specific server."""
    if server_name not in current_user.servers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server '{server_name}' not found",
        )

    server = current_user.servers[server_name]
    return ServerInfo(
        name=server.name,
        status=server.status.value,
        version=server.version,
        port=server.port if server.version else None,
        ip=server.ip if server.version else None,
    )


@router.post("/", response_model=ServerInfo, status_code=status.HTTP_201_CREATED)
async def create_server(
    server_data: ServerCreate,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
) -> ServerInfo:
    """Create a new server."""
    # Check cooldown
    require_operation_cooldown(current_user.id, "server_create")

    # Check if server already exists
    if server_data.name in current_user.servers:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Server '{server_data.name}' already exists",
        )

    # Create server instance
    server = Server(name=server_data.name, user=current_user)
    current_user.add_server(server)

    # Set cooldown for server creation
    set_operation_cooldown(current_user.id, "server_create")

    # Install server in background
    def install_server_task() -> None:
        try:
            server.install(server_data.version)
        except Exception as e:
            logger.error(f"Failed to install server {server_data.name}: {e}")

    background_tasks.add_task(install_server_task)

    return ServerInfo(
        name=server.name,
        status="installing",
        version=server_data.version,
        port=None,
        ip=None,
    )


@router.put("/{server_name}", response_model=ServerInfo)
async def update_server(
    server_name: str,
    update_data: ServerUpdate,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
) -> ServerInfo:
    """Update server to a new version."""
    # Check cooldown
    require_operation_cooldown(current_user.id, "server_update")

    if server_name not in current_user.servers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server '{server_name}' not found",
        )

    server = current_user.servers[server_name]

    # Set cooldown for server update
    set_operation_cooldown(current_user.id, "server_update")

    # Update in background
    def update_server_task() -> None:
        try:
            server.update(update_data.version)
        except Exception as e:
            logger.error(f"Failed to update server {server_name}: {e}")

    background_tasks.add_task(update_server_task)

    return ServerInfo(
        name=server.name,
        status="updating",
        version=update_data.version,
        port=server.port if server.version else None,
        ip=server.ip if server.version else None,
    )


@router.delete("/{server_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_server(server_name: str, current_user: CurrentUser) -> None:
    """Delete a server."""
    if server_name not in current_user.servers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server '{server_name}' not found",
        )

    server = current_user.servers[server_name]
    current_user.remove_server(server)


@router.post("/{server_name}/start", response_model=ServerStatus)
async def start_server(server_name: str, current_user: CurrentUser) -> ServerStatus:
    """Start a server."""
    if server_name not in current_user.servers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server '{server_name}' not found",
        )

    server = current_user.servers[server_name]

    try:
        server.start()
        return ServerStatus(
            status=server.status.value,
            container_id=server.container.id if server.container else None,
        )
    except Exception as e:
        logger.error(f"Failed to start server {server_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start server: {str(e)}",
        ) from e


@router.post("/{server_name}/stop", response_model=ServerStatus)
async def stop_server(server_name: str, current_user: CurrentUser) -> ServerStatus:
    """Stop a server."""
    if server_name not in current_user.servers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server '{server_name}' not found",
        )

    server = current_user.servers[server_name]

    try:
        server.stop()
        return ServerStatus(
            status=server.status.value,
            container_id=server.container.id if server.container else None,
        )
    except Exception as e:
        logger.error(f"Failed to stop server {server_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop server: {str(e)}",
        ) from e


@router.post("/{server_name}/restart", response_model=ServerStatus)
async def restart_server(server_name: str, current_user: CurrentUser) -> ServerStatus:
    """Restart a server."""
    if server_name not in current_user.servers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server '{server_name}' not found",
        )

    server = current_user.servers[server_name]

    try:
        server.restart()
        return ServerStatus(
            status=server.status.value,
            container_id=server.container.id if server.container else None,
        )
    except Exception as e:
        logger.error(f"Failed to restart server {server_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart server: {str(e)}",
        ) from e


@router.get("/{server_name}/status", response_model=ServerStatus)
async def get_server_status(server_name: str, current_user: CurrentUser) -> ServerStatus:
    """Get current server status."""
    if server_name not in current_user.servers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server '{server_name}' not found",
        )

    server = current_user.servers[server_name]
    return ServerStatus(
        status=server.status.value,
        container_id=server.container.id if server.container else None,
    )


@router.get("/{server_name}/logs")
async def get_server_logs(
    server_name: str,
    current_user: CurrentUser,
    previous: bool = False,
) -> dict[str, str]:
    """Get server logs."""
    if server_name not in current_user.servers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server '{server_name}' not found",
        )

    server = current_user.servers[server_name]
    log_file = server.previous_log_file if previous else server.current_log_file

    if not log_file.exists():
        return {"logs": ""}

    try:
        # Read last 200KB of log file
        with log_file.open("rb") as f:
            f.seek(0, 2)  # Seek to end
            file_size = f.tell()
            if file_size > 204800:  # 200KB
                f.seek(file_size - 204800)
            content = f.read().decode("utf-8", errors="replace")
        return {"logs": content}
    except Exception as e:
        logger.error(f"Failed to read logs for {server_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read server logs",
        ) from e
