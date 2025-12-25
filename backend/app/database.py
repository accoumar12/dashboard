"""Database connection and session management."""

import logging
from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)

# Global engine variable
engine: AsyncEngine | None = None
async_session_factory: sessionmaker | None = None


def _create_engine(database_url: str, is_sqlite: bool = False) -> AsyncEngine:
    """Create async engine for the given database URL.

    Args:
        database_url: Database connection URL.
        is_sqlite: Whether this is a SQLite database.

    Returns:
        AsyncEngine configured for the database.
    """
    connect_args = {}
    if is_sqlite:
        # SQLite-specific connection arguments
        connect_args = {"check_same_thread": False}

    return create_async_engine(
        database_url,
        echo=settings.debug,
        future=True,
        connect_args=connect_args if is_sqlite else {},
    )


async def initialize_database() -> tuple[AsyncEngine, bool]:
    """Initialize database connection with automatic fallback.

    Tries PostgreSQL first, then falls back to SQLite playground if enabled.

    Returns:
        Tuple of (engine, is_playground) where is_playground indicates if using SQLite.
    """
    global engine, async_session_factory

    # Try PostgreSQL first
    try:
        pg_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
        test_engine = _create_engine(pg_url, is_sqlite=False)

        # Test connection
        async with test_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

        engine = test_engine
        async_session_factory = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        logger.info("Connected to PostgreSQL database")
        return engine, False

    except Exception as e:
        logger.warning(f"PostgreSQL connection failed: {e}")

        # Fallback to SQLite playground if enabled
        if settings.use_playground_db:
            playground_path = Path(settings.playground_db_path)

            if not playground_path.exists():
                logger.error(f"Playground database not found at {playground_path}")
                raise RuntimeError(
                    "No database available. Run: python scripts/create_playground_db.py"
                )

            sqlite_url = f"sqlite+aiosqlite:///{playground_path}"
            engine = _create_engine(sqlite_url, is_sqlite=True)
            async_session_factory = sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

            logger.info(f"Using SQLite playground database at {playground_path}")
            return engine, True
        else:
            logger.error("PostgreSQL unavailable and playground database disabled")
            raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session.

    Yields:
        AsyncSession: Database session.
    """
    if async_session_factory is None:
        raise RuntimeError("Database not initialized")

    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def test_connection() -> bool:
    """Test database connection.

    Returns:
        True if connection is successful, False otherwise.
    """
    try:
        if engine is None:
            return False
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
