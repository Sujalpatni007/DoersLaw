"""
DOER Platform - Authentication Service

This module provides JWT authentication utilities including:
- Password hashing with bcrypt
- JWT token generation and validation
- Current user dependency injection

PRODUCTION UPGRADES:
1. Use Redis for token blacklisting (logout invalidation)
2. Implement refresh token rotation for better security
3. Add rate limiting on login attempts
4. Consider OAuth2/OIDC integration for enterprise
5. Add 2FA support with TOTP
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models import User, UserRole
from app.schemas import TokenPayload

settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token extraction from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate bcrypt hash for a password."""
    return pwd_context.hash(password)


def create_access_token(user_id: int, role: str) -> str:
    """
    Create a JWT access token.
    
    Args:
        user_id: User's database ID
        role: User's role string
        
    Returns:
        Encoded JWT token
    """
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
        "type": "access"
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    """
    Create a JWT refresh token.
    
    PRODUCTION: Store refresh tokens in Redis with user session tracking
    to enable:
    - Token invalidation on logout
    - Session management (view/revoke active sessions)
    - Refresh token rotation
    """
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh"
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[TokenPayload]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        TokenPayload if valid, None if invalid
    """
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        return TokenPayload(
            sub=payload.get("sub"),
            exp=datetime.fromtimestamp(payload.get("exp")),
            role=payload.get("role", "client")
        )
    except JWTError:
        return None


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    FastAPI dependency to get the current authenticated user.
    
    Usage:
        @router.get("/protected")
        async def protected_route(current_user: User = Depends(get_current_user)):
            return {"user": current_user.email}
    
    PRODUCTION: Add token blacklist check with Redis:
        if await redis.sismember(f"blacklist:{user_id}", token):
            raise HTTPException(status_code=401, detail="Token has been revoked")
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = decode_token(token)
    if token_data is None:
        raise credentials_exception
    
    # Fetch user from database
    result = await db.execute(select(User).where(User.id == int(token_data.sub)))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency that ensures user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


def require_role(*roles: UserRole):
    """
    Dependency factory for role-based access control.
    
    Usage:
        @router.get("/admin-only")
        async def admin_route(
            current_user: User = Depends(require_role(UserRole.ADMIN))
        ):
            return {"message": "Admin access granted"}
    """
    async def role_checker(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {', '.join([r.value for r in roles])}"
            )
        return current_user
    return role_checker


async def authenticate_user(
    db: AsyncSession, 
    email: str, 
    password: str
) -> Optional[User]:
    """
    Authenticate a user with email and password.
    
    PRODUCTION: Add rate limiting and account lockout after failed attempts:
        failed_attempts = await redis.incr(f"login_attempts:{email}")
        if failed_attempts > 5:
            raise HTTPException(429, "Too many login attempts. Try again later.")
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    
    return user
