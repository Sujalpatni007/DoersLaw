"""
DOER Platform - Authentication Router

Handles user registration, login, token refresh, and profile management.

PRODUCTION UPGRADES:
- Add rate limiting on login attempts (use slowapi or Redis-based limiter)
- Implement email verification flow
- Add OAuth2 (Google, Microsoft) login options
- Add password reset via email
- Implement 2FA with TOTP
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, UserRole
from app.schemas import (
    UserCreate, UserResponse, UserUpdate, UserLogin,
    Token, TokenRefresh, MessageResponse
)
from app.services.auth import (
    get_password_hash, authenticate_user,
    create_access_token, create_refresh_token, decode_token,
    get_current_user
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account.
    
    - **email**: Valid email address (must be unique)
    - **password**: Minimum 8 characters
    - **full_name**: User's full name
    - **phone**: Optional phone number for SMS notifications
    
    PRODUCTION: Add email verification requirement before account activation
    """
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        phone=user_data.phone,
        role=user_data.role,
        is_active=True,
        is_verified=False,  # PRODUCTION: Set to False until email verified
        created_at=datetime.utcnow()
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # PRODUCTION: Send verification email here
    # await send_verification_email(user.email, generate_verification_token(user.id))
    
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens.
    
    Uses OAuth2 password flow for compatibility with standard clients.
    Returns both access token (short-lived) and refresh token (long-lived).
    
    PRODUCTION:
    - Add rate limiting (e.g., 5 attempts per minute per IP)
    - Log failed login attempts for security monitoring
    - Implement account lockout after repeated failures
    """
    user = await authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        # PRODUCTION: Log failed attempt with IP address
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Update last login timestamp
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Generate tokens
    access_token = create_access_token(user.id, user.role.value)
    refresh_token = create_refresh_token(user.id)
    
    # PRODUCTION: Store refresh token hash in Redis for tracking
    # await redis.setex(f"refresh_token:{user.id}", refresh_token_expires, token_hash)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using a valid refresh token.
    
    PRODUCTION:
    - Implement refresh token rotation (issue new refresh token on each use)
    - Check refresh token against Redis blacklist
    - Log token refresh for security audit
    """
    payload = decode_token(token_data.refresh_token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Verify user still exists and is active
    result = await db.execute(select(User).where(User.id == int(payload.sub)))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Generate new tokens
    access_token = create_access_token(user.id, user.role.value)
    refresh_token = create_refresh_token(user.id)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get the currently authenticated user's profile.
    
    Requires valid access token in Authorization header.
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update the current user's profile information.
    
    Only allows updating: full_name, phone
    Email and password changes require separate endpoints for security.
    """
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    if user_update.phone is not None:
        current_user.phone = user_update.phone
    
    current_user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(current_user)
    
    return current_user


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: User = Depends(get_current_user)
):
    """
    Logout the current user.
    
    PRODUCTION: Add token to Redis blacklist to prevent reuse:
        await redis.sadd(f"blacklist:{current_user.id}", current_token)
        await redis.expire(f"blacklist:{current_user.id}", ACCESS_TOKEN_EXPIRE_SECONDS)
    
    For now, client should discard the token.
    """
    # In a stateless JWT setup, logout is handled client-side
    # PRODUCTION: Implement token blacklisting with Redis
    
    return MessageResponse(
        message="Successfully logged out. Please discard your tokens.",
        success=True
    )
