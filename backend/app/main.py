"""FastAPI application entry point."""

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import test_connection
from app.models import DatabaseSchemaModel, QueryRequest, QueryResponse
from app.query_builder import execute_table_query
from app.schema_inspector import analyze_schema

logger = logging.getLogger(__name__)

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

    Initializes database connection on application startup.
    """
    logger.info("Starting SQL Dashboard API...")
    try:
        from app.database import initialize_database

        _, is_playground = await initialize_database()
        if is_playground:
            logger.info("✓ Using SQLite playground database")
        else:
            logger.info("✓ Connected to PostgreSQL database")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        logger.warning("Application started but database is unavailable")


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


@app.get("/api/schema", response_model=DatabaseSchemaModel)
async def get_schema() -> DatabaseSchemaModel:
    """Get database schema information.

    Returns:
        DatabaseSchemaModel containing all tables, columns, and relationships.

    Raises:
        HTTPException: If schema analysis fails.
    """
    try:
        from app.database import engine

        if engine is None:
            raise HTTPException(
                status_code=503, detail="Database not initialized"
            )

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
    except Exception as e:
        logger.error(f"Failed to analyze schema: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze database schema")


@app.post("/api/query", response_model=QueryResponse)
async def query_table(request: QueryRequest) -> QueryResponse:
    """Execute a filtered and paginated query on a table.

    Args:
        request: Query request with table, filters, sort, and pagination.

    Returns:
        QueryResponse with data, total count, offset, and limit.

    Raises:
        HTTPException: If query execution fails.
    """
    try:
        from app.database import engine

        if engine is None:
            raise HTTPException(
                status_code=503, detail="Database not initialized"
            )

        return await execute_table_query(engine, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        raise HTTPException(status_code=500, detail="Query execution failed")
