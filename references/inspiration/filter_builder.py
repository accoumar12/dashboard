from __future__ import annotations

import inspect
from collections.abc import Sequence
from inspect import Parameter, signature

from sqlalchemy import (
    ColumnElement,
    ColumnOperators,
    Select,
    and_,
    desc,
    or_,
    select,
    Column,
)
from sqlalchemy import inspect as sql_inspect
from sqlalchemy.sql import true as sql_true

from cockpit.common.exceptions import BadRequestException
from cockpit.common.orm.base import Base
from cockpit.common.orm.tables import TABLES
from cockpit.common.schema import (
    ColumnFilter,
    FilterOperator,
    InputFilter,
    Order,
    QueryFilter,
    TableInputFilter,
)
from cockpit.database.core import engine, session


def build_where_clause(query_filter: QueryFilter | None) -> ColumnElement[bool] | None:
    if query_filter is None:
        return None
    where_clauses = []
    for sub_filter in query_filter.filters:
        if isinstance(sub_filter, ColumnFilter):
            Table = TABLES[sub_filter.table]
            try:
                column = getattr(Table, sub_filter.column)
            except AttributeError:
                raise BadRequestException(
                    f"Column {sub_filter.column} not found in table {sub_filter.table}"
                )

            column_operator = getattr(column, sub_filter.operator)
            if sub_filter.value:
                where_clauses.append(
                    column_operator(sub_filter.value, **sub_filter.options)
                )
            else:
                where_clauses.append(column_operator(**sub_filter.options))
        elif isinstance(sub_filter, QueryFilter) and not sub_filter.is_empty():
            where_clauses.append(build_where_clause(sub_filter))

    if query_filter.filter_operator is FilterOperator.AND:
        return and_(*where_clauses)
    else:
        return or_(*where_clauses)


def _get_column_operators_methods():
    """Extract all public methods from ColumnOperators class with their docstrings."""
    methods = {}

    for name in dir(ColumnOperators):
        if (
            not name.startswith("_") and name != "__hash__" and name != "operate"
        ):  # Exclude private methods and operate
            attr = getattr(ColumnOperators, name)
            if callable(attr):
                # Get the docstring from the method
                doc = inspect.getdoc(attr) or f"SQLAlchemy {name} operator"
                methods[name] = doc

    return methods


def build_column_predicate(col_filter: ColumnFilter) -> ColumnElement[bool]:
    try:
        Table = TABLES[col_filter.table]
    except KeyError as e:
        raise BadRequestException(f"Table {e.args[0]} not found")

    try:
        column = getattr(Table, col_filter.column)
    except AttributeError:
        raise BadRequestException(
            f"Column {col_filter.column} not found in table {col_filter.table}"
        )

    return build_base_column_predicate(
        column, col_filter.operator, col_filter.value, col_filter.options
    )


def build_base_column_predicate(
    column: Column, operator: str, value: str, options: dict
) -> ColumnElement[bool]:
    column_operator = getattr(column, operator)
    sig = signature(column_operator)
    # count the number of args without default values excluding **kw
    args_count = len(
        [
            p
            for p in sig.parameters.values()
            if p.default == Parameter.empty and p.kind != Parameter.VAR_KEYWORD
        ]
    )
    if args_count == 0:
        return column_operator(**options)
    elif args_count == 1:
        return column_operator(value, **options)
    elif args_count > 1 and isinstance(value, list) and len(value) == args_count:
        return column_operator(*value, **options)

    raise BadRequestException(
        f"Invalid number of arguments for operator {operator} in column {column.name} in table {column.table}"
    )


def _is_association_table(tablename: str) -> bool:
    """Check if a table is an association table (not a mapped ORM class)."""
    return tablename not in [cls.__tablename__ for cls in TABLES.values() if hasattr(cls, "__tablename__")]


def _get_fk_graph():
    """Build a directed graph of foreign-key relationships using the database inspector.

    Each edge is represented as a tuple (from_table, to_table, pairs),
    where pairs is a list of (from_col, to_col) column-name tuples.
    Both directions are included (child->parent and parent->child).

    For association tables (many-to-many), creates direct edges between the connected tables.
    """
    insp = sql_inspect(engine)
    graph: dict[str, list[tuple[str, str, list[tuple[str, str]]]]] = {}

    # Ensure all tables appear as keys
    try:
        table_names = insp.get_table_names()
    except Exception:
        # Fall back to using ORM known tables if inspector cannot list them (unlikely in tests)
        table_names = [cls.__tablename__ for cls in TABLES.values()]

    # First pass: identify association tables and build connections through them
    association_tables: dict[str, list[dict]] = {}
    for t in table_names:
        if _is_association_table(t):
            try:
                fks = insp.get_foreign_keys(t)
            except Exception:
                fks = []
            if len(fks) >= 2:  # Association table should have at least 2 FKs
                association_tables[t] = fks

    # Second pass: build graph including direct connections through association tables
    for t in table_names:
        graph.setdefault(t, [])

        # Skip association tables in the graph (we'll connect through them)
        if _is_association_table(t):
            continue

        try:
            fks = insp.get_foreign_keys(t)
        except Exception:
            fks = []
        for fk in fks:
            ref_table = fk.get("referred_table")
            local_cols = fk.get("constrained_columns") or []
            remote_cols = fk.get("referred_columns") or []
            if not ref_table or not local_cols or not remote_cols:
                continue
            pairs = list(zip(local_cols, remote_cols))
            # forward edge: local(child) -> referred(parent)
            graph.setdefault(t, []).append((t, ref_table, pairs))
            # reverse edge: referred(parent) -> local(child)
            rev_pairs = [(b, a) for a, b in pairs]
            graph.setdefault(ref_table, []).append((ref_table, t, rev_pairs))

    # Third pass: add direct edges through association tables
    for assoc_table, fks in association_tables.items():
        # For each pair of FKs in the association table, create a direct connection
        for i, fk1 in enumerate(fks):
            for fk2 in fks[i+1:]:
                table1 = fk1.get("referred_table")
                table2 = fk2.get("referred_table")
                if not table1 or not table2:
                    continue

                # Create bidirectional edges with empty pairs (indicating many-to-many)
                # We use empty pairs because the actual FK columns are in the association table
                graph.setdefault(table1, []).append((table1, table2, []))
                graph.setdefault(table2, []).append((table2, table1, []))

    return graph


def _find_fk_path(
    graph: dict[str, list[tuple[str, str, list[tuple[str, str]]]]], src: str, dst: str
):
    """BFS to find a path of edges from src table to dst table. Returns list of edges."""
    if src == dst:
        return []
    from collections import deque

    queue = deque([src])
    visited = {src}
    parent: dict[str, tuple[str, tuple[str, str, list[tuple[str, str]]]]] = {}

    while queue:
        cur = queue.popleft()
        for edge in graph.get(cur, []):
            _from, to, _pairs = edge
            if to in visited:
                continue
            visited.add(to)
            parent[to] = (cur, edge)
            if to == dst:
                # reconstruct path
                path: list[tuple[str, str, list[tuple[str, str]]]] = []
                node = dst
                while node != src:
                    prev, e = parent[node]
                    path.append(e)
                    node = prev
                path.reverse()
                return path
            queue.append(to)
    return None


def _table_by_tablename(name: str) -> type[Base]:
    for cls in TABLES.values():
        if getattr(cls, "__tablename__", None) == name:
            return cls
    raise BadRequestException(f"Unknown table name {name}")


essentially_true = and_(sql_true())  # neutral element for AND


def _reorient_path_to_forward(path_edges: list[tuple[str, str, list[tuple[str, str]]]]):
    """Given a path that may go from target->other, reorient to other->target.

    Returns a list of edges (from_name, to_name, pairs) directed from other to target.
    """
    if not path_edges:
        return []
    # path_edges are already contiguous; if the first edge 'from' is the source (other), keep as is.
    return path_edges


def _exists_via_fk_path(
    target_table: type[Base], other_table: type[Base], other_pred: ColumnElement[bool]
):
    graph = _get_fk_graph()
    other_name = other_table.__tablename__
    target_name = target_table.__tablename__

    path = _find_fk_path(graph, other_name, target_name)
    reversed_used = False
    if path is None:
        # try reverse then invert each edge to forward orientation
        rev_path = _find_fk_path(graph, target_name, other_name)
        if rev_path is None:
            raise BadRequestException(
                f"Cannot correlate {target_table.__name__} with {other_table.__name__} — no FK path found"
            )
        reversed_used = True
        # Invert each edge to get forward other->target
        forward_path = []
        for frm, to, pairs in reversed(rev_path):
            # current edge is A->B (towards other), we need B->A
            inv_pairs = [(b, a) for a, b in pairs]
            forward_path.append((to, frm, inv_pairs))
        path = forward_path

    if not path:
        # same table
        return other_pred

    # Special case: direct many-to-many relationship (single edge with empty pairs)
    if len(path) == 1 and not path[0][2]:
        # This is a many-to-many relationship through an association table
        # We need to find the association table and build a proper EXISTS through it
        return _exists_via_association_table(target_table, other_table, other_pred)

    # Build a SELECT with joins along the path except the final hop to target; correlate the last hop to target.
    # Start from other_table
    subq = select(1)
    subq = subq.select_from(other_table)

    # track current table class of the chain
    chain_cur_cls = other_table

    # join through intermediate tables (edges[:-1])
    for frm, to, pairs in path[:-1]:
        to_cls = _table_by_tablename(to)
        onclause = (
            and_(*[getattr(chain_cur_cls, a) == getattr(to_cls, b) for a, b in pairs])
            if pairs
            else sql_true()
        )
        subq = subq.join(to_cls, onclause)
        chain_cur_cls = to_cls

    # last edge from chain_cur_cls to target
    last_pairs = path[-1][2]
    if last_pairs:
        # Standard FK correlation on the final hop
        final_corr = and_(
            *[
                getattr(chain_cur_cls, a) == getattr(target_table, b)
                for a, b in last_pairs
            ]
        )
        subq = subq.where(and_(other_pred, final_corr))
        return subq.exists()
    else:
        # The final hop is a many-to-many through an association table.
        # We must join the association table between chain_cur_cls and target_table,
        # and then correlate to target_table via the association FKs.
        insp = sql_inspect(engine)
        from_name = getattr(chain_cur_cls, "__tablename__", None)
        target_name = target_table.__tablename__

        try:
            table_names = insp.get_table_names()
        except Exception:
            table_names = []

        assoc_found = False
        for assoc_table_name in table_names:
            if not _is_association_table(assoc_table_name):
                continue
            try:
                fks = insp.get_foreign_keys(assoc_table_name)
            except Exception:
                continue

            ref_tables = [fk.get("referred_table") for fk in fks]
            if from_name in ref_tables and target_name in ref_tables:
                # Found an association table connecting chain_cur_cls and target_table
                from_fk = next((fk for fk in fks if fk.get("referred_table") == from_name), None)
                target_fk = next((fk for fk in fks if fk.get("referred_table") == target_name), None)
                if not from_fk or not target_fk:
                    continue

                from sqlalchemy import Table as SQLATable, MetaData
                metadata = MetaData()
                assoc_table = SQLATable(assoc_table_name, metadata, autoload_with=engine)

                # Join association on the "from" side (chain_cur_cls)
                from_onclause = and_(
                    *[
                        getattr(chain_cur_cls, remote_col) == assoc_table.c[local_col]
                        for local_col, remote_col in zip(
                            from_fk.get("constrained_columns", []),
                            from_fk.get("referred_columns", []),
                        )
                    ]
                )
                subq = subq.join(assoc_table, from_onclause)

                # Correlate association to the target_table
                final_corr = and_(
                    *[
                        assoc_table.c[local_col] == getattr(target_table, remote_col)
                        for local_col, remote_col in zip(
                            target_fk.get("constrained_columns", []),
                            target_fk.get("referred_columns", []),
                        )
                    ]
                )

                subq = subq.where(and_(other_pred, final_corr))
                assoc_found = True
                break

        if not assoc_found:
            raise BadRequestException(
                f"Cannot correlate {target_table.__name__} with {chain_cur_cls.__name__} — association table not found"
            )
        return subq.exists()


def _exists_via_association_table(
    target_table: type[Base], other_table: type[Base], other_pred: ColumnElement[bool]
):
    """Build an EXISTS subquery through an association table for many-to-many relationships."""
    insp = sql_inspect(engine)
    target_name = target_table.__tablename__
    other_name = other_table.__tablename__

    # Find the association table that connects target and other
    try:
        table_names = insp.get_table_names()
    except Exception:
        table_names = []

    for assoc_table_name in table_names:
        if not _is_association_table(assoc_table_name):
            continue

        try:
            fks = insp.get_foreign_keys(assoc_table_name)
        except Exception:
            continue

        # Check if this association table connects our two tables
        ref_tables = [fk.get("referred_table") for fk in fks]
        if target_name in ref_tables and other_name in ref_tables:
            # Found the association table!
            # Get the FK details for both sides
            target_fk = next((fk for fk in fks if fk.get("referred_table") == target_name), None)
            other_fk = next((fk for fk in fks if fk.get("referred_table") == other_name), None)

            if not target_fk or not other_fk:
                continue

            # Build the EXISTS subquery
            from sqlalchemy import Table as SQLATable, MetaData
            metadata = MetaData()
            assoc_table = SQLATable(assoc_table_name, metadata, autoload_with=engine)

            subq = select(1).select_from(other_table)
            subq = subq.join(
                assoc_table,
                and_(*[
                    getattr(other_table, remote_col) == assoc_table.c[local_col]
                    for local_col, remote_col in zip(
                        other_fk.get("constrained_columns", []),
                        other_fk.get("referred_columns", [])
                    )
                ])
            )
            subq = subq.where(
                and_(
                    other_pred,
                    *[
                        assoc_table.c[local_col] == getattr(target_table, remote_col)
                        for local_col, remote_col in zip(
                            target_fk.get("constrained_columns", []),
                            target_fk.get("referred_columns", [])
                        )
                    ]
                )
            )
            return subq.exists()

    raise BadRequestException(
        f"Cannot find association table connecting {target_table.__name__} with {other_table.__name__}"
    )


def _build_exists_predicate_for_target(
    target_table: type[Base], query_filter: QueryFilter | ColumnFilter
) -> ColumnElement[bool]:
    """
     converts a tree of filters that may target many tables into a single SQLAlchemy boolean predicate
      on a chosen target table by turning cross-table conditions
       into correlated EXISTS subqueries following the foreign‑key path(s) between tables.

    - If a filter targets the same table as target_table, apply it directly on target_table columns.
    - Otherwise, wrap the per-table predicate inside an EXISTS(select 1 from other_table where predicate and correlation conditions following FK path).
    """
    if isinstance(query_filter, ColumnFilter):
        try:
            other_table = TABLES[query_filter.table]
        except KeyError as e:
            raise BadRequestException(f"Table {e.args[0]} not found")

        predicate = build_column_predicate(query_filter)
        if other_table is target_table:
            return predicate
        else:
            return _exists_via_fk_path(target_table, other_table, predicate)

    # QueryFilter
    sub_preds = []
    for sub in query_filter.filters:
        # Skip empty nested groups
        if isinstance(sub, QueryFilter) and sub.is_empty():
            continue
        sub_preds.append(_build_exists_predicate_for_target(target_table, sub))

    if not sub_preds:
        # No constraints
        return essentially_true

    if query_filter.filter_operator is FilterOperator.AND:
        return and_(*sub_preds)
    else:
        return or_(*sub_preds)


def build_filter_stmt(table: type[Base], input_filter: InputFilter) -> Select:
    stmt = select(table).where(table.study_id == input_filter.study_id)

    # Apply filter tree using EXISTS-based predicates to avoid heavy joins and allow cross-table filters
    if input_filter.query_filter and not input_filter.query_filter.is_empty():
        where_pred = _build_exists_predicate_for_target(
            table, input_filter.query_filter
        )
        stmt = stmt.where(where_pred)
    return stmt


def get_filtered_table(
    table: type[Base], input_filter: TableInputFilter
) -> Sequence[Base]:
    stmt = build_filter_stmt(table, input_filter)

    if input_filter.order_by:
        stmt = stmt.order_by(
            *[
                getattr(table, o.column)
                if o.order is Order.ASC
                else desc(getattr(table, o.column))
                for o in input_filter.order_by
            ]
        )

    stmt = stmt.offset(input_filter.offset).limit(input_filter.limit)

    return session.scalars(stmt).all()
