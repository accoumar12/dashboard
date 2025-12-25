#!/bin/bash
# Load sample schema and data into PostgreSQL database

set -e

# Get database URL from environment or use default
DATABASE_URL="${APP_DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/dashboard}"

echo "Loading sample schema..."
psql "$DATABASE_URL" -f backend/test_data/sample_schema.sql

echo "Loading sample data..."
psql "$DATABASE_URL" -f backend/test_data/sample_data.sql

echo "✓ Sample data loaded successfully!"
echo "Tables created: users, posts"
echo "Sample data: 5 users, 50+ posts"
