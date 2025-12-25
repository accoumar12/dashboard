-- Sample test data for the SQL Dashboard
-- Must be run after sample_schema.sql

-- Insert users
INSERT INTO users (name, email, created_at) VALUES
    ('Alice Johnson', 'alice@example.com', '2024-01-15 10:00:00'),
    ('Bob Smith', 'bob@example.com', '2024-01-20 14:30:00'),
    ('Charlie Brown', 'charlie@example.com', '2024-02-01 09:15:00'),
    ('Diana Prince', 'diana@example.com', '2024-02-10 16:45:00'),
    ('Eve Adams', 'eve@example.com', '2024-03-05 11:20:00');

-- Insert posts
INSERT INTO posts (user_id, title, content, published, created_at) VALUES
    (1, 'Getting Started with SQL', 'SQL is a powerful language for managing databases...', true, '2024-01-16 10:30:00'),
    (1, 'Advanced Query Techniques', 'In this post, we explore advanced SQL queries...', true, '2024-01-25 14:00:00'),
    (1, 'Draft: Database Design Patterns', 'This is a draft about design patterns...', false, '2024-02-05 09:00:00'),
    (2, 'Introduction to PostgreSQL', 'PostgreSQL is an excellent open-source database...', true, '2024-01-22 11:00:00'),
    (2, 'Working with Indexes', 'Indexes can dramatically improve query performance...', true, '2024-02-15 15:30:00'),
    (3, 'My First Blog Post', 'Hello world! This is my first post...', true, '2024-02-02 10:00:00'),
    (3, 'SQL vs NoSQL', 'Comparing different database paradigms...', true, '2024-02-20 13:45:00'),
    (4, 'Data Modeling Best Practices', 'Here are some tips for effective data modeling...', true, '2024-02-11 12:00:00'),
    (4, 'Draft: Future of Databases', 'Exploring upcoming database technologies...', false, '2024-03-01 16:00:00'),
    (5, 'SQL Dashboard Tutorial', 'Learn how to build an interactive SQL dashboard...', true, '2024-03-06 10:30:00');

-- Add some more posts to test pagination
INSERT INTO posts (user_id, title, content, published, created_at)
SELECT
    (RANDOM() * 4 + 1)::INTEGER,
    'Test Post ' || generate_series,
    'This is test content for post ' || generate_series,
    RANDOM() > 0.3,
    CURRENT_TIMESTAMP - (RANDOM() * INTERVAL '90 days')
FROM generate_series(1, 40);
