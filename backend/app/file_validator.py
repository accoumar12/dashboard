"""SQLite file validation utilities."""

import tempfile
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.exceptions import UploadValidationError

# SQLite magic bytes - first 16 bytes of every SQLite database
SQLITE_MAGIC_BYTES = b"SQLite format 3\x00"


async def validate_sqlite_file(file: UploadFile) -> tuple[bool, str | None]:
    """Validate that the uploaded file is a valid SQLite database.

    Performs multiple validation checks:
    1. File extension validation
    2. Magic bytes verification
    3. Database connection test

    Args:
        file: The uploaded file to validate.

    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is None.
    """
    # Check file extension
    if not file.filename:
        return False, "No filename provided"

    filename_lower = file.filename.lower()
    if not filename_lower.endswith((".db", ".sqlite", ".sqlite3")):
        return (
            False,
            "Invalid file extension. Only .db, .sqlite, .sqlite3 are allowed",
        )

    # Read magic bytes
    header = await file.read(16)
    await file.seek(0)  # Reset for later reading

    if not header.startswith(SQLITE_MAGIC_BYTES):
        return False, "Invalid SQLite file format (magic bytes mismatch)"

    # Test database connection
    try:
        temp_path = Path(tempfile.gettempdir()) / f"validate_{uuid4()}.db"

        # Write to temporary file
        content = await file.read()
        await file.seek(0)  # Reset for later reading

        temp_path.write_bytes(content)

        # Try to connect and execute a simple query
        engine = create_async_engine(f"sqlite+aiosqlite:///{temp_path}")
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        finally:
            await engine.dispose()

        # Clean up temporary file
        temp_path.unlink()

        return True, None

    except Exception as e:
        return False, f"Database validation failed: {str(e)}"


async def validate_file_size(
    file: UploadFile, max_size_mb: int
) -> tuple[bool, str | None]:
    """Validate that the uploaded file is within size limits.

    Args:
        file: The uploaded file to validate.
        max_size_mb: Maximum allowed file size in megabytes.

    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is None.
    """
    # Get file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset

    max_size_bytes = max_size_mb * 1024 * 1024

    if file_size > max_size_bytes:
        size_mb = file_size / (1024 * 1024)
        return False, f"File too large ({size_mb:.1f}MB). Maximum size: {max_size_mb}MB"

    return True, None


async def validate_upload(file: UploadFile, max_size_mb: int) -> None:
    """Validate an uploaded database file.

    Performs all validation checks and raises UploadValidationError if any fail.

    Args:
        file: The uploaded file to validate.
        max_size_mb: Maximum allowed file size in megabytes.

    Raises:
        UploadValidationError: If validation fails.
    """
    # Validate file size
    is_valid, error = await validate_file_size(file, max_size_mb)
    if not is_valid:
        raise UploadValidationError(error or "File size validation failed")

    # Validate SQLite format
    is_valid, error = await validate_sqlite_file(file)
    if not is_valid:
        raise UploadValidationError(error or "SQLite validation failed")
