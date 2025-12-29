"""FastAPI application entry point."""

import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import test_connection
from app.models import DatabaseSchemaModel, QueryRequest, QueryResponse
from app.query_builder import execute_table_query
from app.relationship_graph import RelationshipGraph
from app.schema_inspector import analyze_schema

logger = logging.getLogger(__name__)

# Global cache for relationship graph
_relationship_graph: RelationshipGraph | None = None

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

    Initializes database connection and builds relationship graph.
    """
    global _relationship_graph

    logger.info("Starting SQL Dashboard API...")
    try:
        from app import database

        _, is_playground = await database.initialize_database()
        if is_playground:
            logger.info("✓ Using SQLite playground database")
        else:
            logger.info("✓ Connected to PostgreSQL database")

        # Build relationship graph
        if database.engine:
            logger.info("Building relationship graph...")
            schema = await analyze_schema(database.engine)
            _relationship_graph = RelationshipGraph(schema)
            logger.info(f"✓ Built relationship graph with {len(schema.relationships)} relationships")
        else:
            logger.warning("Engine is None, cannot build relationship graph")

    except Exception as e:
        logger.error(f"Failed to initialize: {e}", exc_info=True)
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
        from app import database

        if database.engine is None:
            raise HTTPException(
                status_code=503, detail="Database not initialized"
            )

        schema = await analyze_schema(database.engine)
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


@app.get("/api/column-values/{table}/{column}")
async def get_column_values(table: str, column: str, limit: int = 100) -> dict[str, list[Any]]:
    """Get distinct values for a column.

    Args:
        table: Table name.
        column: Column name.
        limit: Maximum number of distinct values to return.

    Returns:
        Dictionary with 'values' key containing list of distinct values.

    Raises:
        HTTPException: If query execution fails.
    """
    try:
        from app import database
        from sqlalchemy import MetaData, select, func

        if database.engine is None:
            raise HTTPException(
                status_code=503, detail="Database not initialized"
            )

        # Load table metadata
        metadata = MetaData()
        async with database.engine.connect() as conn:
            await conn.run_sync(
                lambda sync_conn: metadata.reflect(
                    sync_conn, only=[table], views=True
                )
            )

        if table not in metadata.tables:
            raise HTTPException(status_code=404, detail=f"Table '{table}' not found")

        table_obj = metadata.tables[table]

        if column not in table_obj.c:
            raise HTTPException(
                status_code=404, detail=f"Column '{column}' not found in table '{table}'"
            )

        # Query distinct values
        query = (
            select(table_obj.c[column])
            .distinct()
            .where(table_obj.c[column].isnot(None))
            .limit(limit)
        )

        async with database.engine.connect() as conn:
            result = await conn.execute(query)
            rows = result.fetchall()
            values = [row[0] for row in rows]

        return {"values": values}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get column values: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get column values")


@app.post("/api/query", response_model=QueryResponse)
async def query_table(request: QueryRequest) -> QueryResponse:
    """Execute a filtered and paginated query on a table.

    Supports both direct and cross-table filtering via relationship graph.

    Args:
        request: Query request with table, filters, sort, and pagination.

    Returns:
        QueryResponse with data, total count, offset, and limit.

    Raises:
        HTTPException: If query execution fails.
    """
    try:
        from app import database

        if database.engine is None:
            raise HTTPException(
                status_code=503, detail="Database not initialized"
            )

        return await execute_table_query(database.engine, request, _relationship_graph)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Query execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Query execution failed")
