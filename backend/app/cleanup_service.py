"""Background cleanup service for expired database sessions."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from app.config import Settings
from app.session_manager import SessionManager

logger = logging.getLogger(__name__)


class CleanupService:
    """Background service to delete expired database sessions.

    Runs periodically to clean up sessions that haven't been accessed
    within the expiry period.
    """

    def __init__(self, session_manager: SessionManager, settings: Settings) -> None:
        """Initialize the cleanup service.

        Args:
            session_manager: The session manager instance.
            settings: Application settings.
        """
        self.session_manager = session_manager
        self.expiry_days = settings.session_expiry_days
        self.interval_hours = settings.cleanup_interval_hours
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the cleanup background task."""
        self._task = asyncio.create_task(self._cleanup_loop())
        logger.info(
            f"Cleanup service started (expiry: {self.expiry_days} days, "
            f"interval: {self.interval_hours}h)"
        )

    async def stop(self) -> None:
        """Stop the cleanup background task."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            logger.info("Cleanup service stopped")

    async def _cleanup_loop(self) -> None:
        """Main cleanup loop that runs periodically."""
        while True:
            try:
                await asyncio.sleep(self.interval_hours * 3600)
                await self._cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}", exc_info=True)

    async def _cleanup_expired_sessions(self) -> None:
        """Delete expired sessions based on last accessed time."""
        now = datetime.now(timezone.utc)
        expiry_threshold = now - timedelta(days=self.expiry_days)

        logger.info("Starting cleanup of expired sessions...")

        # Get all sessions
        sessions = await self.session_manager.list_sessions()

        expired_sessions = []
        for session in sessions:
            if session.last_accessed < expiry_threshold:
                expired_sessions.append(session.session_id)

        # Delete expired sessions
        deleted_count = 0
        for session_id in expired_sessions:
            try:
                await self.session_manager.delete_session(session_id)
                deleted_count += 1
                logger.info(f"Deleted expired session: {session_id}")
            except Exception as e:
                logger.error(f"Failed to delete session {session_id}: {e}")

        if deleted_count > 0:
            logger.info(f"Cleanup complete: {deleted_count} sessions deleted")
        else:
            logger.debug("Cleanup complete: no expired sessions found")


# Global cleanup service instance
cleanup_service: CleanupService | None = None
