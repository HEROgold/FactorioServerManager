"""Authentication API endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import User, get_db
from backend.schemas import LoginRequest, TokenResponse, User as UserSchema
from backend.security import create_access_token, CurrentUser
from FSM._types import FactorioInterface

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    """Authenticate user with Factorio credentials and return JWT token."""
    fi = FactorioInterface()

    try:
        # Authenticate with Factorio API
        auth_response = await fi.get_auth_token(login_data.email, login_data.password)

        # Check for authentication errors
        if "error" in auth_response:
            error_msg = auth_response.get("message", "Authentication failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_msg,
            )

        # Get or create user
        factorio_token = auth_response[0] if isinstance(auth_response, list) else auth_response.get("token")
        if not factorio_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to obtain Factorio token",
            )

        # Fetch or create user in database
        user = User.fetch_by_email(login_data.email)
        user.persist_factorio_token(factorio_token)

        # Create JWT token
        access_token = create_access_token(data={"sub": user.id, "email": user.email})

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user.id,
            email=user.email,
            display_name=user.display_name,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error",
        ) from e
    finally:
        await fi.aio_http_session.close()


@router.get("/me", response_model=UserSchema)
async def get_current_user_info(current_user: CurrentUser) -> UserSchema:
    """Get current authenticated user information."""
    return UserSchema(
        id=current_user.id,
        email=current_user.email,
        display_name=current_user.display_name,
    )


@router.post("/logout")
async def logout(current_user: CurrentUser) -> dict[str, str]:
    """Logout user (client should discard token)."""
    return {"message": "Successfully logged out"}
