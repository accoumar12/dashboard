import asyncio
from app import database
from app.schema_inspector import analyze_schema
from app.relationship_graph import RelationshipGraph
from app.models import ColumnFilter, QueryRequest
from app.query_builder import execute_table_query

async def test():
    # Initialize database
    await database.initialize_database()

    if not database.engine:
        print("No engine!")
        return
    
    # Build relationship graph
    schema = await analyze_schema(database.engine)
    graph = RelationshipGraph(schema)

    # Test: Filter products by category name
    request = QueryRequest(
        table="products",
        filters=[
            ColumnFilter(table="categories", column="name", operator="contains", value="Books")
        ],
        offset=0,
        limit=50
    )

    print(f"Testing cross-table filter: products filtered by categories.name contains 'Books'")

    result = await execute_table_query(database.engine, request, graph)
    
    print(f"\nResults: {result.total} rows")
    for row in result.data:
        print(f"  Product: {row.get('name')}, category_id: {row.get('category_id')}")

asyncio.run(test())
