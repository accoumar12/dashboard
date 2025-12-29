"""Session management for multi-user database access."""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.config import Settings
from app.exceptions import InvalidSessionError, SessionNotFoundError

logger = logging.getLogger(__name__)


@dataclass
class DatabaseSession:
    """Represents an uploaded database session.

    Attributes:
        session_id: Unique session identifier.
        file_path: Path to the SQLite database file.
        engine: SQLAlchemy async engine for this session.
        created_at: Timestamp when session was created.
        last_accessed: Timestamp when session was last accessed.
        file_size_bytes: Size of the database file in bytes.
        original_filename: Original name of the uploaded file.
    """

    session_id: str
    file_path: Path
    engine: AsyncEngine
    created_at: datetime
    last_accessed: datetime
    file_size_bytes: int
    original_filename: str


class SessionManager:
    """Manages database sessions for multiple users.

    Provides thread-safe access to database sessions, with special handling
    for the playground database.
    """

    def __init__(self) -> None:
        """Initialize the SessionManager."""
        self._sessions: dict[str, DatabaseSession] = {}
        self._playground_session: DatabaseSession | None = None
        self._lock = asyncio.Lock()
        self._settings: Settings | None = None

    async def initialize(self, settings: Settings) -> None:
        """Initialize the session manager with playground database.

        Args:
            settings: Application settings.

        Raises:
            RuntimeError: If playground database initialization fails.
        """
        self._settings = settings

        # Initialize playground session
        playground_path = Path(settings.playground_db_path)

        if not playground_path.exists():
            raise RuntimeError(
                f"Playground database not found at {playground_path}. "
                "Run: python scripts/create_playground_db.py"
            )

        # Create engine for playground
        sqlite_url = f"sqlite+aiosqlite:///{playground_path}"
        engine = create_async_engine(
            sqlite_url,
            echo=settings.debug,
            future=True,
            connect_args={"check_same_thread": False},
        )

        file_size = playground_path.stat().st_size
        now = datetime.now(timezone.utc)

        self._playground_session = DatabaseSession(
            session_id="playground",
            file_path=playground_path,
            engine=engine,
            created_at=now,
            last_accessed=now,
            file_size_bytes=file_size,
            original_filename="playground.db",
        )

        logger.info("Session manager initialized with playground database")

    async def create_session(
        self, file_path: Path, original_filename: str, session_id: str | None = None
    ) -> str:
        """Create a new database session.

        Args:
            file_path: Path to the SQLite database file.
            original_filename: Original name of the uploaded file.
            session_id: Optional session ID to use. If not provided, generates a new one.

        Returns:
            The session ID for the new session.

        Raises:
            InvalidSessionError: If session creation fails.
        """
        if self._settings is None:
            raise RuntimeError("SessionManager not initialized")

        if session_id is None:
            session_id = str(uuid4())
        else:
            session_id = str(session_id)

        try:
            # Create engine for this session
            sqlite_url = f"sqlite+aiosqlite:///{file_path}"
            engine = create_async_engine(
                sqlite_url,
                echo=self._settings.debug,
                future=True,
                connect_args={"check_same_thread": False},
            )

            file_size = file_path.stat().st_size
            now = datetime.now(timezone.utc)

            session = DatabaseSession(
                session_id=session_id,
                file_path=file_path,
                engine=engine,
                created_at=now,
                last_accessed=now,
                file_size_bytes=file_size,
                original_filename=original_filename,
            )

            async with self._lock:
                self._sessions[session_id] = session

            logger.info(f"Created session {session_id} for file {original_filename}")
            return session_id

        except Exception as e:
            logger.error(f"Failed to create session: {e}", exc_info=True)
            raise InvalidSessionError(session_id, str(e))

    async def get_engine(self, session_id: str) -> AsyncEngine:
        """Get the database engine for a session.

        Args:
            session_id: The session ID to retrieve.

        Returns:
            The AsyncEngine for the session.

        Raises:
            SessionNotFoundError: If the session ID is not found.
        """
        # Check playground session first
        if session_id == "playground":
            if self._playground_session is None:
                raise SessionNotFoundError(session_id)
            # Update last accessed time
            self._playground_session.last_accessed = datetime.now(timezone.utc)
            return self._playground_session.engine

        # Check user sessions
        async with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                raise SessionNotFoundError(session_id)

            # Update last accessed time
            session.last_accessed = datetime.now(timezone.utc)
            return session.engine

    async def get_session(self, session_id: str) -> DatabaseSession:
        """Get a database session by ID.

        Args:
            session_id: The session ID to retrieve.

        Returns:
            The DatabaseSession object.

        Raises:
            SessionNotFoundError: If the session ID is not found.
        """
        if session_id == "playground":
            if self._playground_session is None:
                raise SessionNotFoundError(session_id)
            self._playground_session.last_accessed = datetime.now(timezone.utc)
            return self._playground_session

        async with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                raise SessionNotFoundError(session_id)

            session.last_accessed = datetime.now(timezone.utc)
            return session

    async def delete_session(self, session_id: str) -> None:
        """Delete a database session.

        Disposes the engine and deletes the database file.
        Does not allow deletion of playground session.

        Args:
            session_id: The session ID to delete.

        Raises:
            SessionNotFoundError: If the session ID is not found.
            InvalidSessionError: If attempting to delete playground session.
        """
        if session_id == "playground":
            raise InvalidSessionError(
                session_id, "Cannot delete playground session"
            )

        async with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                raise SessionNotFoundError(session_id)

            # Dispose engine
            await session.engine.dispose()

            # Delete file
            try:
                session.file_path.unlink(missing_ok=True)
            except Exception as e:
                logger.warning(
                    f"Failed to delete file {session.file_path}: {e}"
                )

            # Remove from sessions
            del self._sessions[session_id]

        logger.info(f"Deleted session {session_id}")

    async def list_sessions(self) -> list[DatabaseSession]:
        """List all active sessions (excluding playground).

        Returns:
            List of DatabaseSession objects.
        """
        async with self._lock:
            return list(self._sessions.values())

    async def shutdown(self) -> None:
        """Shutdown all database sessions.

        Disposes all engines but does not delete files.
        """
        logger.info("Shutting down session manager")

        # Dispose playground engine
        if self._playground_session:
            await self._playground_session.engine.dispose()

        # Dispose all user session engines
        async with self._lock:
            for session in self._sessions.values():
                try:
                    await session.engine.dispose()
                except Exception as e:
                    logger.error(
                        f"Error disposing engine for session {session.session_id}: {e}"
                    )

        logger.info("Session manager shutdown complete")


# Global session manager instance
session_manager = SessionManager()
