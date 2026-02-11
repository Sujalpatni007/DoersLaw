"""
DOER Platform - Database Configuration

This module sets up the async SQLAlchemy database connection.
Currently configured for SQLite for local development.

PRODUCTION UPGRADE:
1. Install asyncpg: pip install asyncpg
2. Change DATABASE_URL in config.py or .env to:
   postgresql+asyncpg://user:password@host:5432/doer_db
3. For connection pooling, consider:
   - Set pool_size=20, max_overflow=10 in create_async_engine
   - Use PgBouncer for additional connection management
4. Add Alembic for database migrations:
   pip install alembic
   alembic init alembic
   alembic revision --autogenerate -m "Initial migration"
   alembic upgrade head
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

settings = get_settings()

# Create async engine
# PRODUCTION: Add pool_size=20, max_overflow=10 for PostgreSQL
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Set to False in production
    # PRODUCTION PostgreSQL settings:
    # pool_size=20,
    # max_overflow=10,
    # pool_pre_ping=True,  # Verify connections before use
    # pool_recycle=3600,   # Recycle connections after 1 hour
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def get_db() -> AsyncSession:
    """
    Dependency that provides an async database session.
    
    Usage in FastAPI:
        async def my_endpoint(db: AsyncSession = Depends(get_db)):
            ...
    
    The session is automatically closed after the request completes.
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize the database by creating all tables.
    
    PRODUCTION: Use Alembic migrations instead of create_all().
    This is only suitable for development/demo purposes.
    """
    async with engine.begin() as conn:
        # Import models to register them with SQLAlchemy
        from app import models  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Cleanup database connections on shutdown."""
    await engine.dispose()
