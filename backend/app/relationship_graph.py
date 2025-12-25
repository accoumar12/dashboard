"""Relationship graph for finding paths between tables via foreign keys.

This module provides a graph-based representation of database relationships
to support cross-table filtering.
"""

from collections import defaultdict, deque
from dataclasses import dataclass

from app.schema_inspector import DatabaseSchema


@dataclass
class Edge:
    """A directed edge in the relationship graph.

    Represents a foreign key relationship from one table to another.

    Attributes:
        from_table: Source table name.
        to_table: Target table name.
        from_columns: List of source column names.
        to_columns: List of target column names.
    """

    from_table: str
    to_table: str
    from_columns: list[str]
    to_columns: list[str]


@dataclass
class Path:
    """A path between two tables through foreign key relationships.

    Attributes:
        edges: List of edges that form the path.
        tables: List of table names in order (including start and end).
    """

    edges: list[Edge]
    tables: list[str]


class RelationshipGraph:
    """Graph representation of foreign key relationships.

    Provides methods to find paths between tables for cross-table filtering.
    """

    def __init__(self, schema: DatabaseSchema) -> None:
        """Initialize the relationship graph from database schema.

        Args:
            schema: Database schema with tables and relationships.
        """
        # Build bidirectional adjacency list
        self.edges: dict[str, list[Edge]] = defaultdict(list)

        for rel in schema.relationships:
            # Forward edge (from -> to)
            forward_edge = Edge(
                from_table=rel.from_table,
                to_table=rel.to_table,
                from_columns=rel.from_columns,
                to_columns=rel.to_columns,
            )
            self.edges[rel.from_table].append(forward_edge)

            # Reverse edge (to -> from) for bidirectional traversal
            reverse_edge = Edge(
                from_table=rel.to_table,
                to_table=rel.from_table,
                from_columns=rel.to_columns,
                to_columns=rel.from_columns,
            )
            self.edges[rel.to_table].append(reverse_edge)

    def find_path(self, from_table: str, to_table: str) -> Path | None:
        """Find the shortest path between two tables using BFS.

        Args:
            from_table: Starting table name.
            to_table: Target table name.

        Returns:
            Path object if a path exists, None otherwise.
        """
        if from_table == to_table:
            return Path(edges=[], tables=[from_table])

        if from_table not in self.edges:
            return None

        # BFS to find shortest path
        queue: deque[tuple[str, list[Edge]]] = deque([(from_table, [])])
        visited: set[str] = {from_table}

        while queue:
            current_table, path_edges = queue.popleft()

            # Explore neighbors
            for edge in self.edges[current_table]:
                if edge.to_table in visited:
                    continue

                new_path = path_edges + [edge]

                # Found target
                if edge.to_table == to_table:
                    tables = [from_table] + [e.to_table for e in new_path]
                    return Path(edges=new_path, tables=tables)

                # Continue search
                visited.add(edge.to_table)
                queue.append((edge.to_table, new_path))

        return None

    def get_related_tables(self, table: str) -> list[str]:
        """Get all tables directly related to the given table.

        Args:
            table: Table name to find relationships for.

        Returns:
            List of related table names.
        """
        if table not in self.edges:
            return []

        return [edge.to_table for edge in self.edges[table]]
