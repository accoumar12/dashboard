"""Query builder for executing filtered and paginated table queries."""

from sqlalchemy import MetaData, Table, and_, exists, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.models import ColumnFilter, QueryRequest, QueryResponse, SortConfig
from app.relationship_graph import RelationshipGraph


async def execute_table_query(
    engine: AsyncEngine, request: QueryRequest, relationship_graph: RelationshipGraph | None = None
) -> QueryResponse:
    """Execute a filtered and paginated query on a table.

    Args:
        engine: SQLAlchemy async engine.
        request: Query request with table, filters, sort, and pagination.
        relationship_graph: Optional relationship graph for cross-table filtering.

    Returns:
        QueryResponse with data, total count, offset, and limit.

    Raises:
        ValueError: If table doesn't exist or column is invalid.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"=== Query Request ===")
    logger.info(f"  Table: {request.table}")
    logger.info(f"  Filters: {request.filters}")
    logger.info(f"  Relationship graph: {relationship_graph is not None}")

    # Collect all tables needed for filtering
    tables_needed = {request.table}
    for filter_spec in request.filters:
        tables_needed.add(filter_spec.table)

        # For cross-table filters, also add intermediate tables from the path
        if filter_spec.table != request.table and relationship_graph:
            path = relationship_graph.find_path(request.table, filter_spec.table)
            if path:
                # Add all tables in the path
                tables_needed.update(path.tables)

    # Load table metadata
    metadata = MetaData()

    async with engine.connect() as conn:
        # Reflect all needed tables
        await conn.run_sync(
            lambda sync_conn: metadata.reflect(
                sync_conn, only=list(tables_needed), views=True
            )
        )

    if request.table not in metadata.tables:
        raise ValueError(f"Table '{request.table}' does not exist")

    table = metadata.tables[request.table]

    # Build WHERE clause from filters
    where_clauses = []
    for filter_spec in request.filters:
        # Direct filter on the target table
        if filter_spec.table == request.table:
            if filter_spec.column not in table.c:
                raise ValueError(
                    f"Column '{filter_spec.column}' does not exist in table '{request.table}'"
                )

            column = table.c[filter_spec.column]
            value = filter_spec.value

            # Apply operator
            where_clauses.append(_build_filter_expression(column, filter_spec.operator, value))

        # Cross-table filter (requires relationship graph)
        elif relationship_graph:
            # Find path from request table to filter table
            path = relationship_graph.find_path(request.table, filter_spec.table)

            if not path:
                raise ValueError(
                    f"No relationship path found from '{request.table}' to '{filter_spec.table}'"
                )

            # Log the path for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Cross-table filter: {request.table} -> {filter_spec.table}")
            logger.info(f"  Path: {path.tables}")
            logger.info(f"  Filter: {filter_spec.column} {filter_spec.operator} {filter_spec.value}")

            # Build EXISTS subquery
            exists_clause = _build_exists_subquery(
                metadata, table, path, filter_spec
            )
            logger.info(f"  EXISTS clause: {exists_clause}")
            where_clauses.append(exists_clause)

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


def _build_filter_expression(column, operator: str, value):
    """Build a SQLAlchemy filter expression from operator and value.

    Args:
        column: SQLAlchemy column object.
        operator: Filter operator string.
        value: Filter value.

    Returns:
        SQLAlchemy filter expression.

    Raises:
        ValueError: If operator is unknown.
    """
    if operator == "eq":
        return column == value
    elif operator == "ne":
        return column != value
    elif operator == "gt":
        return column > value
    elif operator == "lt":
        return column < value
    elif operator == "gte":
        return column >= value
    elif operator == "lte":
        return column <= value
    elif operator == "contains":
        return column.ilike(f"%{value}%")
    elif operator == "startswith":
        return column.ilike(f"{value}%")
    elif operator == "endswith":
        return column.ilike(f"%{value}")
    elif operator == "is_null":
        return column.is_(None)
    elif operator == "is_not_null":
        return column.isnot(None)
    else:
        raise ValueError(f"Unknown operator: {operator}")


def _build_exists_subquery(metadata: MetaData, base_table: Table, path, filter_spec: ColumnFilter):
    """Build an EXISTS subquery for cross-table filtering.

    Args:
        metadata: SQLAlchemy metadata with reflected tables.
        base_table: The base table being queried.
        path: Path object with edges connecting tables.
        filter_spec: Filter specification to apply.

    Returns:
        SQLAlchemy EXISTS clause.

    Raises:
        ValueError: If filter column doesn't exist in target table.
    """
    # Get the target table (last table in path)
    target_table = metadata.tables[filter_spec.table]

    if filter_spec.column not in target_table.c:
        raise ValueError(
            f"Column '{filter_spec.column}' does not exist in table '{filter_spec.table}'"
        )

    # Build the subquery by joining through the path
    # Start with the target table
    subquery = select(text("1")).select_from(target_table)

    # Apply the filter on the target table
    filter_column = target_table.c[filter_spec.column]
    filter_expr = _build_filter_expression(filter_column, filter_spec.operator, filter_spec.value)
    subquery = subquery.where(filter_expr)

    # Add JOIN conditions for each edge in the path (in reverse)
    current_table = target_table
    for edge in reversed(path.edges):
        # Get the other table in the edge
        if edge.to_table == current_table.name:
            # We're going from to_table back to from_table
            other_table = metadata.tables[edge.from_table]

            # Join condition: current_table.to_columns = other_table.from_columns
            for to_col, from_col in zip(edge.to_columns, edge.from_columns):
                subquery = subquery.where(
                    current_table.c[to_col] == other_table.c[from_col]
                )
        else:
            # We're going from from_table to to_table
            other_table = metadata.tables[edge.to_table]

            # Join condition: current_table.from_columns = other_table.to_columns
            for from_col, to_col in zip(edge.from_columns, edge.to_columns):
                subquery = subquery.where(
                    current_table.c[from_col] == other_table.c[to_col]
                )

        current_table = other_table

    # Final join condition to base table
    # current_table should now be the base_table or connected to it
    if current_table.name != base_table.name:
        # Find the edge that connects to base_table
        for edge in path.edges:
            if edge.from_table == current_table.name and edge.to_table == base_table.name:
                for from_col, to_col in zip(edge.from_columns, edge.to_columns):
                    subquery = subquery.where(
                        current_table.c[from_col] == base_table.c[to_col]
                    )
                break
            elif edge.to_table == current_table.name and edge.from_table == base_table.name:
                for to_col, from_col in zip(edge.to_columns, edge.from_columns):
                    subquery = subquery.where(
                        current_table.c[to_col] == base_table.c[from_col]
                    )
                break

    return exists(subquery)
