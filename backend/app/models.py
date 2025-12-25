"""Pydantic models for API requests and responses."""

from typing import Any

from pydantic import BaseModel, Field


class ColumnInfoModel(BaseModel):
    """Column information model.

    Attributes:
        name: Column name.
        type: Column type as string.
        nullable: Whether the column accepts NULL values.
        primary_key: Whether the column is a primary key.
        default: Default value for the column if any.
    """

    name: str
    type: str
    nullable: bool
    primary_key: bool
    default: str | None = None


class RelationshipInfoModel(BaseModel):
    """Foreign key relationship model.

    Attributes:
        from_table: Source table name.
        from_columns: List of source column names.
        to_table: Target table name.
        to_columns: List of target column names.
    """

    from_table: str
    from_columns: list[str]
    to_table: str
    to_columns: list[str]


class TableInfoModel(BaseModel):
    """Table information model.

    Attributes:
        name: Table name.
        columns: List of column information.
    """

    name: str
    columns: list[ColumnInfoModel]


class DatabaseSchemaModel(BaseModel):
    """Complete database schema model.

    Attributes:
        tables: List of tables in the database.
        relationships: List of foreign key relationships.
    """

    tables: list[TableInfoModel]
    relationships: list[RelationshipInfoModel]


class ColumnFilter(BaseModel):
    """Filter specification for a column.

    Attributes:
        table: Table name to filter.
        column: Column name to filter.
        operator: Filter operator (eq, ne, gt, lt, gte, lte, contains, startswith, endswith).
        value: Value to filter by.
    """

    table: str
    column: str
    operator: str
    value: str | int | float | bool


class SortConfig(BaseModel):
    """Sort configuration.

    Attributes:
        column: Column name to sort by.
        direction: Sort direction (asc or desc).
    """

    column: str
    direction: str = Field(pattern="^(asc|desc)$")


class QueryRequest(BaseModel):
    """Query request model.

    Attributes:
        table: Table name to query.
        filters: Optional list of filters to apply.
        sort: Optional sort configuration.
        offset: Number of rows to skip (for pagination).
        limit: Maximum number of rows to return.
    """

    table: str
    filters: list[ColumnFilter] = Field(default_factory=list)
    sort: SortConfig | None = None
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=1000)


class QueryResponse(BaseModel):
    """Query response model.

    Attributes:
        data: List of row data as dictionaries.
        total: Total number of rows matching the filters.
        offset: Offset used in the query.
        limit: Limit used in the query.
    """

    data: list[dict[str, Any]]
    total: int
    offset: int
    limit: int
