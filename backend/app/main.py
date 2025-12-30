"""FastAPI application entry point."""

import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.cleanup_service import CleanupService
from app.config import settings
from app.database import test_connection
from app.exceptions import SessionNotFoundError, UploadValidationError
from app.file_validator import validate_upload
from app.models import DatabaseSchemaModel, QueryRequest, QueryResponse, UploadResponse
from app.query_builder import execute_table_query
from app.relationship_graph import RelationshipGraph
from app.schema_inspector import analyze_schema
from app.session_manager import session_manager

logger = logging.getLogger(__name__)

# Global cache for relationship graphs (per session)
_relationship_graphs: dict[str, RelationshipGraph] = {}

# Rate limiting for uploads
_upload_tracker: defaultdict[str, list[datetime]] = defaultdict(list)
_RATE_LIMIT_UPLOADS = 10
_RATE_LIMIT_WINDOW_MINUTES = 60

# Cleanup service instance
_cleanup_service: CleanupService | None = None

app = FastAPI(
    title="SQL Dashboard API",
    description="Backend API for the SQL Dashboard application",
    version="0.1.0",
    debug=settings.debug,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    """Startup event handler.

    Initializes session manager with playground database and starts cleanup service.
    """
    global _cleanup_service

    logger.info("Starting SQL Dashboard API...")
    try:
        # Initialize session manager with playground
        await session_manager.initialize(settings)
        logger.info("✓ Session manager initialized")

        # Build relationship graph for playground
        logger.info("Building relationship graph for playground...")
        engine = await session_manager.get_engine("playground")
        schema = await analyze_schema(engine)
        _relationship_graphs["playground"] = RelationshipGraph(schema)
        logger.info(
            f"✓ Built playground relationship graph with {len(schema.relationships)} relationships"
        )

        # Ensure uploads directory exists
        settings.upload_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"✓ Uploads directory ready at {settings.upload_dir}")

        # Start cleanup service
        _cleanup_service = CleanupService(session_manager, settings)
        await _cleanup_service.start()
        logger.info("✓ Cleanup service started")

    except Exception as e:
        logger.error(f"Failed to initialize: {e}", exc_info=True)
        logger.warning("Application started but may have limited functionality")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Shutdown event handler.

    Cleans up all database sessions and stops cleanup service.
    """
    logger.info("Shutting down SQL Dashboard API...")
    try:
        # Stop cleanup service
        if _cleanup_service:
            await _cleanup_service.stop()
            logger.info("✓ Cleanup service stopped")

        # Shutdown session manager
        await session_manager.shutdown()
        logger.info("✓ Session manager shut down")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        A dictionary indicating the service status.
    """
    return {"status": "ok"}


@app.get("/api/db-status")
async def database_status() -> dict[str, bool]:
    """Database connection status endpoint.

    Returns:
        A dictionary indicating whether the database is connected.
    """
    connected = await test_connection()
    return {"connected": connected}


@app.post("/api/upload", response_model=UploadResponse)
async def upload_database(
    request: Request, file: UploadFile = File(...)
) -> UploadResponse:
    """Upload a SQLite database file.

    Creates a new session for the uploaded database and returns a session ID.

    Args:
        request: HTTP request (for rate limiting).
        file: The uploaded SQLite database file.

    Returns:
        UploadResponse with session ID and redirect URL.

    Raises:
        HTTPException: If upload fails validation or rate limit exceeded.
    """
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    now = datetime.now(timezone.utc)

    # Clean old entries
    _upload_tracker[client_ip] = [
        ts
        for ts in _upload_tracker[client_ip]
        if now - ts < timedelta(minutes=_RATE_LIMIT_WINDOW_MINUTES)
    ]

    if len(_upload_tracker[client_ip]) >= _RATE_LIMIT_UPLOADS:
        raise UploadValidationError(
            f"Rate limit exceeded: Max {_RATE_LIMIT_UPLOADS} uploads per {_RATE_LIMIT_WINDOW_MINUTES} minutes."
        )

    try:
        # Check database limit (count all uploaded database files)
        uploaded_db_count = len(list(settings.upload_dir.glob("*.db")))
        if uploaded_db_count >= settings.max_databases:
            raise UploadValidationError(
                f"Maximum number of databases reached ({settings.max_databases}). Please try again later.",
            )

        # Validate upload
        await validate_upload(file, settings.max_upload_size_mb)

        # Generate session ID
        session_id = str(uuid4())

        # Save file with session ID
        content = await file.read()
        file_path = settings.upload_dir / f"{session_id}.db"
        file_path.write_bytes(content)

        # Create session with the generated session_id
        session_id = await session_manager.create_session(
            file_path,
            original_filename=file.filename or "unknown.db",
            session_id=session_id,
        )

        # Build relationship graph for this session
        try:
            engine = await session_manager.get_engine(session_id)
            schema = await analyze_schema(engine)
            _relationship_graphs[session_id] = RelationshipGraph(schema)
            logger.info(f"Built relationship graph for session {session_id}")
        except Exception as e:
            logger.warning(f"Failed to build relationship graph for {session_id}: {e}")
            # Continue anyway - graph is optional

        # Track upload
        _upload_tracker[client_ip].append(now)

        # Calculate expiry
        expiry = now + timedelta(days=settings.session_expiry_days)

        file_size_mb = len(content) / (1024 * 1024)

        logger.info(
            f"Uploaded database: {file.filename} ({file_size_mb:.2f}MB) -> session {session_id}"
        )

        return UploadResponse(
            session_id=session_id,
            redirect_url=f"/db/{session_id}",
            file_size_mb=round(file_size_mb, 2),
            expires_at=expiry.isoformat(),
        )

    except UploadValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Upload failed")


@app.get("/api/{session_id}/schema", response_model=DatabaseSchemaModel)
async def get_schema(session_id: str) -> DatabaseSchemaModel:
    """Get database schema information for a specific session.

    Args:
        session_id: The session ID (or "playground").

    Returns:
        DatabaseSchemaModel containing all tables, columns, and relationships.

    Raises:
        HTTPException: If schema analysis fails or session not found.
    """
    try:
        engine = await session_manager.get_engine(session_id)
        schema = await analyze_schema(engine)

        return DatabaseSchemaModel(
            tables=[
                {
                    "name": table.name,
                    "columns": [
                        {
                            "name": col.name,
                            "type": col.type,
                            "nullable": col.nullable,
                            "primary_key": col.primary_key,
                            "default": col.default,
                        }
                        for col in table.columns
                    ],
                }
                for table in schema.tables
            ],
            relationships=[
                {
                    "from_table": rel.from_table,
                    "from_columns": rel.from_columns,
                    "to_table": rel.to_table,
                    "to_columns": rel.to_columns,
                }
                for rel in schema.relationships
            ],
        )
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    except Exception as e:
        logger.error(f"Failed to analyze schema for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze database schema")


@app.get("/api/{session_id}/column-values/{table}/{column}")
async def get_column_values(
    session_id: str, table: str, column: str, limit: int = 100
) -> dict[str, list[Any]]:
    """Get distinct values for a column in a specific session.

    Args:
        session_id: The session ID (or "playground").
        table: Table name.
        column: Column name.
        limit: Maximum number of distinct values to return.

    Returns:
        Dictionary with 'values' key containing list of distinct values.

    Raises:
        HTTPException: If query execution fails or session not found.
    """
    try:
        from sqlalchemy import MetaData, select

        engine = await session_manager.get_engine(session_id)

        # Load table metadata
        metadata = MetaData()
        async with engine.connect() as conn:
            await conn.run_sync(
                lambda sync_conn: metadata.reflect(sync_conn, only=[table], views=True)
            )

        if table not in metadata.tables:
            raise HTTPException(status_code=404, detail=f"Table '{table}' not found")

        table_obj = metadata.tables[table]

        if column not in table_obj.c:
            raise HTTPException(
                status_code=404,
                detail=f"Column '{column}' not found in table '{table}'",
            )

        # Query distinct values
        query = (
            select(table_obj.c[column])
            .distinct()
            .where(table_obj.c[column].isnot(None))
            .limit(limit)
        )

        async with engine.connect() as conn:
            result = await conn.execute(query)
            rows = result.fetchall()
            values = [row[0] for row in rows]

        return {"values": values}

    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get column values for session {session_id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to get column values")


@app.post("/api/{session_id}/query", response_model=QueryResponse)
async def query_table(session_id: str, request: QueryRequest) -> QueryResponse:
    """Execute a filtered and paginated query on a table in a specific session.

    Supports both direct and cross-table filtering via relationship graph.

    Args:
        session_id: The session ID (or "playground").
        request: Query request with table, filters, sort, and pagination.

    Returns:
        QueryResponse with data, total count, offset, and limit.

    Raises:
        HTTPException: If query execution fails or session not found.
    """
    try:
        engine = await session_manager.get_engine(session_id)
        relationship_graph = _relationship_graphs.get(session_id)

        return await execute_table_query(
            engine,
            request,
            relationship_graph,
            timeout_seconds=settings.query_timeout_seconds,
        )
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            f"Query execution failed for session {session_id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Query execution failed")
