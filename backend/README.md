# SQL Dashboard Backend

Backend API for the SQL Dashboard application, built with FastAPI and SQLAlchemy.

## Features

- FastAPI framework for high-performance async API
- SQLAlchemy 2.0+ for database interactions
- PostgreSQL database support
- CORS middleware for frontend integration
- Type hints and Pydantic models throughout

## Requirements

- Python 3.11+
- PostgreSQL 15+
- uv package manager

## Setup Instructions

### 1. Install Dependencies

This project uses `uv` as the package manager. Install dependencies:

```bash
cd backend
uv sync
```

### 2. Configure Environment

Create a `.env` file in the backend directory:

```bash
# Database connection
APP_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dashboard

# CORS origins (comma-separated)
APP_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Upload limits
APP_MAX_UPLOAD_SIZE_MB=100

# Debug mode
APP_DEBUG=false
```

### 3. Set Up PostgreSQL

Ensure PostgreSQL is running and create the database:

```bash
psql -U postgres
CREATE DATABASE dashboard;
\q
```

### 4. Run the Application

Start the development server:

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

## API Documentation

Once the server is running, visit:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Available Endpoints

### Health Check

```bash
curl http://localhost:8000/api/health
```

Response:
```json
{
  "status": "ok"
}
```

## Development

### Code Quality

Run linting and formatting:

```bash
# Format code
uv run ruff format .

# Check for issues
uv run ruff check .

# Fix auto-fixable issues
uv run ruff check . --fix
```

### Type Checking

```bash
uv run mypy app/
```

### Testing

```bash
uv run pytest
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py          # Package initialization
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database connection (to be added)
│   ├── models.py            # Pydantic models (to be added)
│   ├── schema_inspector.py  # Database schema analysis (to be added)
│   └── query_builder.py     # Query building logic (to be added)
├── tests/                   # Test files (to be added)
├── scripts/                 # Utility scripts (to be added)
├── pyproject.toml           # Project dependencies
├── ruff.toml                # Ruff configuration
└── README.md                # This file
```

## Next Steps

- [ ] Implement database connection module
- [ ] Add schema inspection functionality
- [ ] Create query builder for filtered queries
- [ ] Add file upload endpoint for SQL dumps
- [ ] Implement comprehensive tests

## License

See the main project README for license information.
