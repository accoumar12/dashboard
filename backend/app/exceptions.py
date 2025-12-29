"""Custom exceptions for the SQL Dashboard application."""


class SessionNotFoundError(Exception):
    """Raised when a requested session ID is not found."""

    def __init__(self, session_id: str) -> None:
        """Initialize SessionNotFoundError.

        Args:
            session_id: The session ID that was not found.
        """
        self.session_id = session_id
        super().__init__(f"Session not found: {session_id}")


class InvalidSessionError(Exception):
    """Raised when a session is invalid or corrupted."""

    def __init__(self, session_id: str, reason: str) -> None:
        """Initialize InvalidSessionError.

        Args:
            session_id: The invalid session ID.
            reason: The reason why the session is invalid.
        """
        self.session_id = session_id
        self.reason = reason
        super().__init__(f"Invalid session {session_id}: {reason}")


class UploadValidationError(Exception):
    """Raised when an uploaded file fails validation."""

    def __init__(self, message: str) -> None:
        """Initialize UploadValidationError.

        Args:
            message: The validation error message.
        """
        super().__init__(message)


class FileUploadError(Exception):
    """Raised when a file upload fails."""

    def __init__(self, message: str) -> None:
        """Initialize FileUploadError.

        Args:
            message: The error message.
        """
        super().__init__(message)
