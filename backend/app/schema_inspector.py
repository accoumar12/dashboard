"""Database schema inspection and analysis."""

from dataclasses import dataclass

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncEngine


@dataclass
class ColumnInfo:
    """Information about a database column.

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


@dataclass
class RelationshipInfo:
    """Information about a foreign key relationship.

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


@dataclass
class TableInfo:
    """Information about a database table.

    Attributes:
        name: Table name.
        columns: List of column information.
    """

    name: str
    columns: list[ColumnInfo]


@dataclass
class DatabaseSchema:
    """Complete database schema information.

    Attributes:
        tables: List of tables in the database.
        relationships: List of foreign key relationships.
    """

    tables: list[TableInfo]
    relationships: list[RelationshipInfo]


async def analyze_schema(engine: AsyncEngine) -> DatabaseSchema:
    """Analyze and extract complete database schema.

    Inspects the database to extract table structures, column information,
    and foreign key relationships.

    Args:
        engine: SQLAlchemy async engine connected to the database.

    Returns:
        DatabaseSchema containing all tables and relationships.
    """
    # Use sync inspector with async connection
    def _inspect_schema(connection):
        inspector = inspect(connection)
        tables = []
        relationships = []

        # Extract tables and columns
        for table_name in inspector.get_table_names():
            columns = []
            pk_constraint = inspector.get_pk_constraint(table_name)
            pk_columns = set(pk_constraint.get("constrained_columns", []))

            for col in inspector.get_columns(table_name):
                columns.append(
                    ColumnInfo(
                        name=col["name"],
                        type=str(col["type"]),
                        nullable=col["nullable"],
                        primary_key=col["name"] in pk_columns,
                        default=str(col.get("default")) if col.get("default") else None,
                    )
                )

            tables.append(TableInfo(name=table_name, columns=columns))

        # Extract foreign key relationships
        for table_name in inspector.get_table_names():
            for fk in inspector.get_foreign_keys(table_name):
                relationships.append(
                    RelationshipInfo(
                        from_table=table_name,
                        from_columns=fk["constrained_columns"],
                        to_table=fk["referred_table"],
                        to_columns=fk["referred_columns"],
                    )
                )

        return DatabaseSchema(tables=tables, relationships=relationships)

    # Execute inspection in a synchronous context
    async with engine.connect() as conn:
        schema = await conn.run_sync(_inspect_schema)

    return schema
