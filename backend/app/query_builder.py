"""Query builder for executing filtered and paginated table queries."""

from sqlalchemy import MetaData, Table, and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.models import ColumnFilter, QueryRequest, QueryResponse, SortConfig


async def execute_table_query(
    engine: AsyncEngine, request: QueryRequest
) -> QueryResponse:
    """Execute a filtered and paginated query on a table.

    Args:
        engine: SQLAlchemy async engine.
        request: Query request with table, filters, sort, and pagination.

    Returns:
        QueryResponse with data, total count, offset, and limit.

    Raises:
        ValueError: If table doesn't exist or column is invalid.
    """
    # Load table metadata
    metadata = MetaData()

    async with engine.connect() as conn:
        # Reflect the specific table
        await conn.run_sync(
            lambda sync_conn: metadata.reflect(
                sync_conn, only=[request.table], views=True
            )
        )

    if request.table not in metadata.tables:
        raise ValueError(f"Table '{request.table}' does not exist")

    table = metadata.tables[request.table]

    # Build WHERE clause from filters
    where_clauses = []
    for filter_spec in request.filters:
        # Only apply filters for the target table (direct filters)
        if filter_spec.table != request.table:
            continue

        if filter_spec.column not in table.c:
            raise ValueError(
                f"Column '{filter_spec.column}' does not exist in table '{request.table}'"
            )

        column = table.c[filter_spec.column]
        value = filter_spec.value

        # Map operator to SQLAlchemy expression
        if filter_spec.operator == "eq":
            where_clauses.append(column == value)
        elif filter_spec.operator == "ne":
            where_clauses.append(column != value)
        elif filter_spec.operator == "gt":
            where_clauses.append(column > value)
        elif filter_spec.operator == "lt":
            where_clauses.append(column < value)
        elif filter_spec.operator == "gte":
            where_clauses.append(column >= value)
        elif filter_spec.operator == "lte":
            where_clauses.append(column <= value)
        elif filter_spec.operator == "contains":
            where_clauses.append(column.ilike(f"%{value}%"))
        elif filter_spec.operator == "startswith":
            where_clauses.append(column.ilike(f"{value}%"))
        elif filter_spec.operator == "endswith":
            where_clauses.append(column.ilike(f"%{value}"))
        elif filter_spec.operator == "is_null":
            where_clauses.append(column.is_(None))
        elif filter_spec.operator == "is_not_null":
            where_clauses.append(column.isnot(None))
        else:
            raise ValueError(f"Unknown operator: {filter_spec.operator}")

    # Build base query
    query = select(table)
    if where_clauses:
        query = query.where(and_(*where_clauses))

    # Add sorting
    if request.sort:
        if request.sort.column not in table.c:
            raise ValueError(
                f"Sort column '{request.sort.column}' does not exist in table '{request.table}'"
            )

        sort_column = table.c[request.sort.column]
        if request.sort.direction == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

    # Add pagination
    query = query.offset(request.offset).limit(request.limit)

    # Count query
    count_query = select(func.count()).select_from(table)
    if where_clauses:
        count_query = count_query.where(and_(*where_clauses))

    # Execute queries
    async with engine.connect() as conn:
        # Get total count
        count_result = await conn.execute(count_query)
        total = count_result.scalar() or 0

        # Get data
        result = await conn.execute(query)
        rows = result.fetchall()

        # Convert to list of dicts
        data = [dict(row._mapping) for row in rows]

    return QueryResponse(data=data, total=total, offset=request.offset, limit=request.limit)
