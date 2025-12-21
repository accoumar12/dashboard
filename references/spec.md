# SQL Dashboard Application - Technical Specification

## 1. Project Overview

A minimal, web-based SQL dashboard application that allows users to upload PostgreSQL dumps and visualize table data through an interactive, filterable interface. The application emphasizes URL-based state management for easy sharing of filtered views.

### 1.1 Core Principles
- **Minimal**: Focus on essential features, avoid over-engineering
- **Shareable**: Complete state preserved in URL
- **Dynamic**: Auto-cascading filters based on database relationships
- **Responsive**: Real-time updates across related tables

## 2. Requirements

### 2.1 Functional Requirements

#### FR1: Database Management
- **FR1.1**: Accept PostgreSQL dump file upload via web interface
- **FR1.2**: Execute dump against PostgreSQL database instance
- **FR1.3**: Support single active dump at a time (new upload replaces existing)
- **FR1.4**: Extract and analyze database schema (tables, columns, foreign keys)
- **FR1.5**: Auto-detect relationships through foreign key constraints

#### FR2: Table Visualization
- **FR2.1**: Display tables as interactive grid widgets
- **FR2.2**: Show all columns by default for each table
- **FR2.3**: Implement infinite scroll for table data loading
- **FR2.4**: Support resizable and rearrangeable grid layout
- **FR2.5**: Provide right sidebar for table selection/toggling

#### FR3: Filtering System
- **FR3.1**: Click column headers to open filter popover
- **FR3.2**: Provide dedicated filter builder panel
- **FR3.3**: Support basic filter operators (equals, contains, greater than, less than, etc.)
- **FR3.4**: Apply simple AND logic across multiple filters
- **FR3.5**: Auto-cascade filters to related tables based on foreign key relationships
- **FR3.6**: Handle many-to-many relationships through association tables
- **FR3.7**: Display active filters with clear visual indicators

#### FR4: Sorting
- **FR4.1**: Single-column sorting via column header clicks
- **FR4.2**: Visual indicator for sort direction (ascending/descending)
- **FR4.3**: Toggle sort direction on repeated clicks

#### FR5: URL State Management
- **FR5.1**: Encode all dashboard state in URL:
  - Visible tables and their positions/sizes
  - All active filters (table, column, operator, value)
  - Sort configuration per table
  - Pagination/scroll state per table
- **FR5.2**: Support deep linking (URL fully reconstructs dashboard state)
- **FR5.3**: Update URL in real-time as state changes
- **FR5.4**: Parse URL on initial load to restore complete state

### 2.2 Non-Functional Requirements

#### NFR1: Performance
- Initial table load: < 500ms for tables with 1000 rows
- Filter application: < 200ms response time
- Infinite scroll batch size: 50 rows
- Schema analysis: < 2s for databases with 50 tables

#### NFR2: Usability
- Intuitive drag-and-drop for widget arrangement
- Clear visual feedback for all interactions
- Responsive design (desktop-first, minimum 1280px width)

#### NFR3: Maintainability
- Type hints required for all Python code
- Google-style docstrings for public APIs
- Component-based React architecture
- Comprehensive test coverage (>80%)

#### NFR4: Security
- Validate SQL dump files before execution
- Prevent SQL injection through parameterized queries
- Sandbox database execution environment
- Input validation on all API endpoints

## 3. System Architecture

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     React Frontend                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Dashboard  │  │  Table Grid  │  │   Sidebar    │  │
│  │   Container  │  │   Widgets    │  │   (Tables)   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│  ┌──────────────┐  ┌──────────────┐                    │
│  │    Filter    │  │  URL State   │                    │
│  │    Builder   │  │   Manager    │                    │
│  └──────────────┘  └──────────────┘                    │
└─────────────────────────────────────────────────────────┘
                            │
                         HTTP/REST
                            │
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Backend                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Upload     │  │   Schema     │  │    Query     │  │
│  │   Handler    │  │   Inspector  │  │   Builder    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│  ┌──────────────┐  ┌──────────────┐                    │
│  │   Filter     │  │  Relationship│                    │
│  │   Engine     │  │   Resolver   │                    │
│  └──────────────┘  └──────────────┘                    │
└─────────────────────────────────────────────────────────┘
                            │
                       PostgreSQL
                            │
┌─────────────────────────────────────────────────────────┐
│                  PostgreSQL Database                     │
│           (Active dump data + metadata)                  │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Technology Stack

#### Backend
- **Framework**: FastAPI 0.100+
- **Database ORM**: SQLAlchemy 2.0+
- **Database**: PostgreSQL 15+
- **Python**: 3.11+
- **Package Manager**: uv

#### Frontend
- **Framework**: React 18+
- **State Management**: TanStack Query (React Query) for server state
- **Routing**: React Router v6+ (for URL state)
- **Grid Layout**: react-grid-layout
- **Tables**: TanStack Table (React Table v8)
- **UI Components**: Radix UI or shadcn/ui (minimal, accessible)
- **Build Tool**: Vite

#### Development Tools
- **Testing (Backend)**: pytest, pytest-asyncio
- **Testing (Frontend)**: Vitest, React Testing Library
- **Type Checking**: mypy (Python), TypeScript (Frontend)
- **Linting**: ruff (Python), ESLint (Frontend)
- **Formatting**: ruff format (Python), Prettier (Frontend)

## 4. Data Model & Schema Detection

### 4.1 Database Schema Inspection

The application uses PostgreSQL's information_schema and SQLAlchemy inspection to:

```python
from sqlalchemy import inspect, MetaData

def analyze_schema(engine):
    """Extract complete database schema information."""
    inspector = inspect(engine)

    schema = {
        'tables': [],
        'relationships': []
    }

    # Extract tables and columns
    for table_name in inspector.get_table_names():
        columns = []
        for col in inspector.get_columns(table_name):
            columns.append({
                'name': col['name'],
                'type': str(col['type']),
                'nullable': col['nullable'],
                'primary_key': col.get('primary_key', False)
            })

        schema['tables'].append({
            'name': table_name,
            'columns': columns
        })

    # Extract foreign key relationships
    for table_name in inspector.get_table_names():
        for fk in inspector.get_foreign_keys(table_name):
            schema['relationships'].append({
                'from_table': table_name,
                'from_columns': fk['constrained_columns'],
                'to_table': fk['referred_table'],
                'to_columns': fk['referred_columns']
            })

    return schema
```

### 4.2 Relationship Graph

Build a bidirectional graph of table relationships:

```python
class RelationshipGraph:
    """Manages foreign key relationships between tables."""

    def __init__(self, relationships: list[dict]):
        self.graph: dict[str, list[Edge]] = {}
        self._build_graph(relationships)

    def find_path(self, source: str, target: str) -> list[Edge] | None:
        """BFS to find FK path between two tables."""
        # Implementation as shown in reference code
        pass

    def get_related_tables(self, table: str) -> list[str]:
        """Get all directly related tables."""
        return [edge.to_table for edge in self.graph.get(table, [])]
```

### 4.3 Association Table Detection

Identify many-to-many relationship tables:

```python
def is_association_table(table_name: str, inspector) -> bool:
    """
    Association table criteria:
    - Not a mapped ORM class (pure junction table)
    - Has at least 2 foreign keys
    - Typically has only FKs and maybe a composite primary key
    """
    fks = inspector.get_foreign_keys(table_name)
    return len(fks) >= 2 and table_name not in MAPPED_TABLES
```

## 5. API Design

### 5.1 Endpoints

#### POST /api/upload
Upload and process PostgreSQL dump file.

**Request:**
```typescript
Content-Type: multipart/form-data
{
  file: File // .sql dump file
}
```

**Response:**
```typescript
{
  success: boolean,
  schema: {
    tables: Array<{
      name: string,
      columns: Array<{
        name: string,
        type: string,
        nullable: boolean,
        primary_key: boolean
      }>
    }>,
    relationships: Array<{
      from_table: string,
      from_columns: string[],
      to_table: string,
      to_columns: string[]
    }>
  },
  error?: string
}
```

#### GET /api/schema
Get current database schema.

**Response:** Same as POST /api/upload schema object.

#### POST /api/query
Execute filtered query on a table.

**Request:**
```typescript
{
  table: string,
  filters?: Array<{
    table: string,
    column: string,
    operator: string, // "eq", "ne", "gt", "lt", "gte", "lte", "contains", "startswith", "endswith"
    value: string | number | boolean
  }>,
  sort?: {
    column: string,
    direction: "asc" | "desc"
  },
  offset: number,
  limit: number
}
```

**Response:**
```typescript
{
  data: Array<Record<string, any>>,
  total: number,
  offset: number,
  limit: number
}
```

#### GET /api/table/{table_name}/count
Get total row count with optional filters.

**Query Parameters:**
```typescript
filters?: string // JSON-encoded filter array
```

**Response:**
```typescript
{
  count: number
}
```

### 5.2 Filter Processing

The backend converts frontend filter specifications into SQLAlchemy queries:

```python
def build_filter_predicate(
    target_table: type[Base],
    filters: list[ColumnFilter],
    relationship_graph: RelationshipGraph
) -> ColumnElement[bool]:
    """
    Build SQLAlchemy WHERE clause with cascading filters.

    For filters on the target table, apply directly.
    For filters on related tables, use correlated EXISTS subqueries.
    """
    predicates = []

    for filter in filters:
        if filter.table == target_table.__tablename__:
            # Direct filter on target table
            column = getattr(target_table, filter.column)
            operator = getattr(column, filter.operator)
            predicates.append(operator(filter.value))
        else:
            # Cross-table filter - build EXISTS subquery
            other_table = get_table_by_name(filter.table)
            path = relationship_graph.find_path(filter.table, target_table.__tablename__)

            if not path:
                raise ValueError(f"No FK path from {filter.table} to {target_table.__tablename__}")

            exists_clause = build_exists_via_path(
                target_table, other_table, path, filter
            )
            predicates.append(exists_clause)

    return and_(*predicates) if predicates else True
```

## 6. Frontend Architecture

### 6.1 Component Structure

```
src/
├── components/
│   ├── Dashboard/
│   │   ├── Dashboard.tsx          # Main container
│   │   ├── TableWidget.tsx        # Individual table widget
│   │   ├── WidgetGrid.tsx         # Grid layout manager
│   │   └── Sidebar.tsx            # Table selection sidebar
│   ├── Filters/
│   │   ├── FilterBuilder.tsx      # Main filter panel
│   │   ├── FilterRow.tsx          # Single filter row
│   │   ├── ColumnFilterPopover.tsx # Column header popover
│   │   └── FilterOperatorSelect.tsx
│   ├── Table/
│   │   ├── DataTable.tsx          # Table with infinite scroll
│   │   ├── TableHeader.tsx        # Sortable/filterable headers
│   │   └── InfiniteScrollLoader.tsx
│   └── Upload/
│       └── UploadForm.tsx         # SQL dump upload
├── hooks/
│   ├── useUrlState.ts             # URL state management
│   ├── useTableData.ts            # Table data fetching
│   ├── useSchema.ts               # Schema management
│   └── useFilters.ts              # Filter state management
├── lib/
│   ├── api.ts                     # API client
│   ├── urlState.ts                # URL encoding/decoding
│   └── types.ts                   # TypeScript definitions
└── App.tsx
```

### 6.2 URL State Management

The URL encodes the complete dashboard state using query parameters:

**URL Format:**
```
/dashboard?state=<base64_encoded_json>
```

**State Object:**
```typescript
interface DashboardState {
  tables: Array<{
    name: string,
    position: { x: number, y: number, w: number, h: number },
    visible: boolean,
    sort?: { column: string, direction: 'asc' | 'desc' },
    scrollOffset: number
  }>,
  filters: Array<{
    table: string,
    column: string,
    operator: string,
    value: any
  }>
}
```

**URL State Hook:**
```typescript
export function useUrlState() {
  const [searchParams, setSearchParams] = useSearchParams();

  const state = useMemo(() => {
    const encoded = searchParams.get('state');
    if (!encoded) return defaultState;

    try {
      const json = atob(encoded);
      return JSON.parse(json);
    } catch {
      return defaultState;
    }
  }, [searchParams]);

  const updateState = useCallback((newState: DashboardState) => {
    const json = JSON.stringify(newState);
    const encoded = btoa(json);
    setSearchParams({ state: encoded }, { replace: true });
  }, [setSearchParams]);

  return [state, updateState] as const;
}
```

### 6.3 Filter Cascading Logic

When a filter is applied, the frontend:
1. Updates the global filter state
2. Encodes new state in URL
3. For each visible table, calls `/api/query` with ALL filters
4. Backend determines which filters apply via FK relationships
5. UI updates all affected tables

```typescript
function useFilteredTableData(
  tableName: string,
  globalFilters: Filter[],
  sort?: Sort,
  offset: number = 0
) {
  return useQuery({
    queryKey: ['table', tableName, globalFilters, sort, offset],
    queryFn: async () => {
      const response = await api.post('/api/query', {
        table: tableName,
        filters: globalFilters, // All filters, backend decides relevance
        sort,
        offset,
        limit: 50
      });
      return response.data;
    }
  });
}
```

### 6.4 Infinite Scroll Implementation

```typescript
function DataTable({ tableName, filters, sort }: DataTableProps) {
  const [offset, setOffset] = useState(0);
  const [allData, setAllData] = useState<any[]>([]);

  const { data, isLoading } = useFilteredTableData(
    tableName,
    filters,
    sort,
    offset
  );

  useEffect(() => {
    if (data) {
      setAllData(prev => [...prev, ...data.data]);
    }
  }, [data]);

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, scrollHeight, clientHeight } = e.currentTarget;

    if (scrollHeight - scrollTop <= clientHeight * 1.5 && !isLoading) {
      setOffset(prev => prev + 50);
    }
  };

  return (
    <div onScroll={handleScroll} className="overflow-auto">
      <Table data={allData} />
      {isLoading && <Spinner />}
    </div>
  );
}
```

## 7. Filter System Design

### 7.1 Supported Operators by Column Type

| Column Type | Operators |
|------------|-----------|
| String | eq, ne, contains, startswith, endswith, is_null, is_not_null |
| Numeric | eq, ne, gt, lt, gte, lte, is_null, is_not_null |
| Boolean | eq, ne |
| Date/Time | eq, ne, gt, lt, gte, lte, is_null, is_not_null |

### 7.2 Filter Builder UI

```
┌─────────────────────────────────────────────┐
│ Filters                                [x]  │
├─────────────────────────────────────────────┤
│ users.name contains "John"            [x]   │
│ orders.total > 100                    [x]   │
│ orders.status equals "shipped"        [x]   │
├─────────────────────────────────────────────┤
│ [+ Add Filter]                              │
└─────────────────────────────────────────────┘
```

### 7.3 Column Header Popover

When clicking a column header:
```
┌─────────────────────────────┐
│ name                    ▼   │
├─────────────────────────────┤
│ Sort Ascending          ↑   │
│ Sort Descending         ↓   │
├─────────────────────────────┤
│ Filter...                   │
│ ┌─────────────────────────┐ │
│ │ Operator: [contains  ▼] │ │
│ │ Value:    [_________  ] │ │
│ │         [Apply Filter]  │ │
│ └─────────────────────────┘ │
└─────────────────────────────┘
```

## 8. Error Handling

### 8.1 Backend Error Responses

```python
class APIException(Exception):
    """Base exception for API errors."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code

class InvalidDumpException(APIException):
    """SQL dump is invalid or cannot be executed."""
    pass

class TableNotFoundException(APIException):
    """Requested table does not exist."""
    pass

class FilterException(APIException):
    """Filter specification is invalid."""
    pass

@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message}
    )
```

### 8.2 Frontend Error Handling

```typescript
function ErrorBoundary({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundaryComponent
      fallback={
        <div className="error-container">
          <h2>Something went wrong</h2>
          <button onClick={() => window.location.reload()}>
            Reload Dashboard
          </button>
        </div>
      }
    >
      {children}
    </ErrorBoundaryComponent>
  );
}

// Query error handling
function TableWidget({ tableName }: { tableName: string }) {
  const { data, error, isLoading } = useTableData(tableName);

  if (error) {
    return (
      <div className="widget-error">
        <p>Failed to load {tableName}</p>
        <button onClick={() => queryClient.invalidateQueries(['table', tableName])}>
          Retry
        </button>
      </div>
    );
  }

  // ... render table
}
```

### 8.3 Validation

**Backend:**
- Validate SQL dump before execution (check for malicious content)
- Validate filter specifications (table exists, column exists, operator valid)
- Sanitize all user input
- Use parameterized queries exclusively

**Frontend:**
- Validate filter values match column types
- Prevent invalid state configurations
- Handle malformed URL states gracefully

## 9. Testing Strategy

### 9.1 Backend Tests

**Unit Tests:**
```python
# test_filter_builder.py
def test_build_direct_filter():
    """Test filtering on the target table directly."""
    filter = ColumnFilter(table="users", column="name", operator="eq", value="John")
    predicate = build_filter_predicate(User, [filter], graph)
    assert str(predicate) contains "users.name = :name_1"

def test_build_cross_table_filter():
    """Test filtering via foreign key relationship."""
    filter = ColumnFilter(table="orders", column="total", operator="gt", value=100)
    predicate = build_filter_predicate(User, [filter], graph)
    assert "EXISTS" in str(predicate)

def test_many_to_many_filter():
    """Test filtering through association table."""
    # Test users filtered by tags through user_tags association
    pass

# test_schema_inspector.py
def test_extract_foreign_keys():
    """Test FK extraction from database."""
    pass

def test_build_relationship_graph():
    """Test relationship graph construction."""
    pass
```

**Integration Tests:**
```python
# test_api.py
@pytest.mark.asyncio
async def test_upload_dump(client, sample_dump):
    """Test SQL dump upload and processing."""
    response = await client.post(
        "/api/upload",
        files={"file": sample_dump}
    )
    assert response.status_code == 200
    assert "schema" in response.json()

@pytest.mark.asyncio
async def test_query_with_filters(client, populated_db):
    """Test querying with cascading filters."""
    response = await client.post(
        "/api/query",
        json={
            "table": "users",
            "filters": [
                {"table": "orders", "column": "status", "operator": "eq", "value": "shipped"}
            ]
        }
    )
    assert response.status_code == 200
    # Verify only users with shipped orders returned
```

### 9.2 Frontend Tests

**Component Tests:**
```typescript
// DataTable.test.tsx
describe('DataTable', () => {
  it('renders column headers', () => {
    render(<DataTable tableName="users" columns={mockColumns} />);
    expect(screen.getByText('name')).toBeInTheDocument();
  });

  it('applies sort on header click', async () => {
    render(<DataTable tableName="users" />);
    await userEvent.click(screen.getByText('name'));
    expect(mockApi.post).toHaveBeenCalledWith(
      '/api/query',
      expect.objectContaining({ sort: { column: 'name', direction: 'asc' }})
    );
  });
});

// FilterBuilder.test.tsx
describe('FilterBuilder', () => {
  it('adds filter when clicking column', async () => {
    // Test filter creation flow
  });

  it('updates URL state when filter added', async () => {
    // Test URL encoding
  });
});
```

**E2E Tests (Playwright/Cypress):**
```typescript
test('complete filter workflow', async ({ page }) => {
  // Upload dump
  await page.goto('/');
  await page.setInputFiles('input[type="file"]', 'test-dump.sql');

  // Add table to dashboard
  await page.click('text=users');
  await expect(page.locator('[data-table="users"]')).toBeVisible();

  // Apply filter
  await page.click('[data-table="users"] [data-column="name"]');
  await page.fill('input[placeholder="Value"]', 'John');
  await page.click('text=Apply Filter');

  // Verify URL updated
  expect(page.url()).toContain('state=');

  // Verify cascading - orders table shows only John's orders
  await page.click('text=orders');
  const orderRows = page.locator('[data-table="orders"] tbody tr');
  // Assert filtered correctly
});
```

### 9.3 Test Data

Create fixture SQL dumps:
```sql
-- fixtures/simple_dump.sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100)
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    total DECIMAL(10, 2),
    status VARCHAR(20)
);

INSERT INTO users (name, email) VALUES
    ('John Doe', 'john@example.com'),
    ('Jane Smith', 'jane@example.com');

INSERT INTO orders (user_id, total, status) VALUES
    (1, 150.00, 'shipped'),
    (1, 75.50, 'pending'),
    (2, 200.00, 'shipped');
```

## 10. Implementation Phases

### Phase 1: Core Infrastructure (Week 1-2)
- [ ] Set up FastAPI project structure
- [ ] Set up React + Vite project
- [ ] PostgreSQL connection and dump execution
- [ ] Schema inspection and relationship graph
- [ ] Basic API endpoints (upload, schema, query)
- [ ] Basic frontend routing and layout

### Phase 2: Table Display (Week 2-3)
- [ ] Table widget component with infinite scroll
- [ ] Grid layout with react-grid-layout
- [ ] Sidebar for table selection
- [ ] Basic styling and responsive design
- [ ] URL state management foundation

### Phase 3: Filtering System (Week 3-4)
- [ ] Filter builder UI component
- [ ] Column header popover
- [ ] Backend filter processing with EXISTS subqueries
- [ ] FK path finding and cascading logic
- [ ] Filter state in URL

### Phase 4: Sorting & Polish (Week 4-5)
- [ ] Column sorting implementation
- [ ] Sort state in URL
- [ ] Error handling and loading states
- [ ] UI polish and animations
- [ ] Performance optimization

### Phase 5: Testing & Documentation (Week 5-6)
- [ ] Unit tests (backend)
- [ ] Component tests (frontend)
- [ ] Integration tests
- [ ] E2E tests
- [ ] User documentation
- [ ] Deployment setup

## 11. Future Enhancements (Out of Scope for MVP)

- **Complex Filter Logic**: AND/OR grouping with nested conditions
- **Multi-column Sorting**: Sort by multiple columns simultaneously
- **Column Visibility**: Show/hide specific columns
- **Visualizations**: Charts, plots, and graphs
- **Data Export**: Export filtered data to CSV/Excel
- **Query History**: Save and recall previous filter combinations
- **Multiple Dumps**: Support multiple concurrent database instances
- **Collaborative Features**: Share dashboards with permissions
- **Custom Calculations**: Computed columns and aggregations
- **Real-time Updates**: WebSocket support for live data

## 12. Development Guidelines

### 12.1 Code Style

**Python:**
- Follow Google Python Style Guide
- Use type hints for all functions
- PEP 8 naming conventions
- Docstrings for all public APIs
- Use `uv` for package management (never `pip`)

**TypeScript:**
- Functional components with hooks
- Explicit typing (avoid `any`)
- ESLint + Prettier configuration
- Named exports for components

### 12.2 Git Workflow

**Commits:**
- Use conventional commits format
- Add `Reported-by:` trailer for user-reported issues
- Add `Github-Issue:#N` trailer for issue references
- Run tests before committing

**Pull Requests:**
- Descriptive titles and body
- Link related issues
- Request review from `accoumar`
- Ensure CI passes

### 12.3 Testing Requirements

- All new features require tests
- Bug fixes require regression tests
- Maintain >80% code coverage
- Run full test suite before PR

## 13. Deployment Considerations

### 13.1 Environment Variables

```bash
# Backend
DATABASE_URL=postgresql://user:pass@localhost:5432/dashboard
SECRET_KEY=<random-secret-key>
ALLOWED_ORIGINS=http://localhost:5173,https://dashboard.example.com
MAX_UPLOAD_SIZE=100MB

# Frontend
VITE_API_URL=http://localhost:8000
```

### 13.2 Docker Setup

```dockerfile
# Backend Dockerfile
FROM python:3.11-slim
RUN pip install uv
WORKDIR /app
COPY . .
RUN uv sync
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0"]

# Frontend Dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
CMD ["npm", "run", "preview"]
```

### 13.3 Production Checklist

- [ ] Enable CORS with specific origins
- [ ] Set up database backups
- [ ] Configure rate limiting
- [ ] Enable HTTPS
- [ ] Set up monitoring and logging
- [ ] Configure file upload limits
- [ ] Implement database connection pooling
- [ ] Add health check endpoints

## 14. Success Criteria

The MVP is complete when:

1. ✓ User can upload a PostgreSQL dump and see the schema
2. ✓ User can add/remove tables to dashboard via sidebar
3. ✓ User can view table data with infinite scroll
4. ✓ User can apply filters via column headers or filter builder
5. ✓ Filters automatically cascade to related tables
6. ✓ User can sort tables by single column
7. ✓ Complete dashboard state is encoded in URL
8. ✓ Shared URLs perfectly recreate dashboard state
9. ✓ Application is responsive and performant
10. ✓ Code has >80% test coverage

## 15. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Large dumps timeout | High | Stream processing, progress indicator, size limits |
| Complex FK paths slow queries | Medium | Query optimization, caching, EXPLAIN analysis |
| URL too long for complex state | Medium | Compression (base64 + gzip), state versioning |
| Infinite scroll memory leak | Medium | Virtualization, data windowing, cleanup |
| Schema detection fails | High | Comprehensive error handling, manual override option |

## 16. Contact & Support

- **Project Owner**: accoumar
- **Issue Tracker**: GitHub Issues
- **Development Guide**: See CLAUDE.md in repository

---

**Document Version**: 1.0
**Last Updated**: 2025-12-21
**Status**: Ready for Implementation
