#!/usr/bin/env python3
"""Create an embedded SQLite playground database with sample e-commerce data.

This script creates a self-contained SQLite database that serves as:
1. A playground for users to explore the dashboard without external database setup
2. A test database for automated testing
3. A demonstration of the dashboard's capabilities
"""

import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path


def create_playground_database(db_path: str = "playground.db") -> None:
    """Create and populate the playground SQLite database.

    Args:
        db_path: Path where the SQLite database file should be created.
    """
    # Remove existing database if it exists
    db_file = Path(db_path)
    if db_file.exists():
        db_file.unlink()
        print(f"Removed existing database at {db_path}")

    # Create connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print(f"Creating playground database at {db_path}...")

    # Create tables
    cursor.executescript(
        """
        -- Customers table
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            country TEXT NOT NULL,
            signup_date DATE NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT 1
        );

        -- Categories table
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT
        );

        -- Products table
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            price DECIMAL(10, 2) NOT NULL,
            stock_quantity INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories (id)
        );

        -- Orders table
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            order_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL CHECK (status IN ('pending', 'shipped', 'delivered', 'cancelled')),
            total_amount DECIMAL(10, 2) NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        );

        -- Order items table (many-to-many relationship)
        CREATE TABLE order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            unit_price DECIMAL(10, 2) NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        );

        -- Create indexes for better query performance
        CREATE INDEX idx_products_category ON products(category_id);
        CREATE INDEX idx_orders_customer ON orders(customer_id);
        CREATE INDEX idx_orders_status ON orders(status);
        CREATE INDEX idx_order_items_order ON order_items(order_id);
        CREATE INDEX idx_order_items_product ON order_items(product_id);
    """
    )

    print("✓ Tables created")

    # Insert customers
    customers = [
        ("Alice Johnson", "alice.johnson@email.com", "United States", "2023-01-15", 1),
        ("Bob Smith", "bob.smith@email.com", "Canada", "2023-02-20", 1),
        ("Charlie Brown", "charlie.brown@email.com", "United Kingdom", "2023-03-10", 1),
        ("Diana Prince", "diana.prince@email.com", "Germany", "2023-04-05", 1),
        ("Eve Adams", "eve.adams@email.com", "France", "2023-05-12", 1),
        ("Frank Castle", "frank.castle@email.com", "United States", "2023-06-18", 1),
        ("Grace Hopper", "grace.hopper@email.com", "Australia", "2023-07-22", 1),
        ("Henry Ford", "henry.ford@email.com", "United States", "2023-08-30", 0),
    ]

    cursor.executemany(
        "INSERT INTO customers (name, email, country, signup_date, is_active) VALUES (?, ?, ?, ?, ?)",
        customers,
    )
    print(f"✓ Inserted {len(customers)} customers")

    # Insert categories
    categories = [
        ("Electronics", "Electronic devices and accessories"),
        ("Books", "Physical and digital books"),
        ("Clothing", "Apparel and fashion items"),
        ("Home & Garden", "Home improvement and garden supplies"),
        ("Sports", "Sports equipment and outdoor gear"),
    ]

    cursor.executemany(
        "INSERT INTO categories (name, description) VALUES (?, ?)", categories
    )
    print(f"✓ Inserted {len(categories)} categories")

    # Insert products
    products = [
        # Electronics
        (1, "Wireless Headphones", 79.99, 45),
        (1, "Smartphone Stand", 24.99, 120),
        (1, "USB-C Cable", 12.99, 200),
        (1, "Portable Charger", 39.99, 67),
        (1, "Bluetooth Speaker", 59.99, 34),
        # Books
        (2, "Python Programming Guide", 45.00, 89),
        (2, "Web Development 101", 38.50, 56),
        (2, "Database Design Patterns", 52.00, 23),
        (2, "Clean Code", 42.00, 78),
        # Clothing
        (3, "Cotton T-Shirt", 19.99, 150),
        (3, "Denim Jeans", 49.99, 87),
        (3, "Running Shoes", 89.99, 45),
        (3, "Winter Jacket", 129.99, 28),
        # Home & Garden
        (4, "Plant Pot Set", 29.99, 92),
        (4, "LED Desk Lamp", 34.99, 61),
        (4, "Kitchen Knife Set", 79.99, 34),
        # Sports
        (5, "Yoga Mat", 24.99, 103),
        (5, "Dumbbell Set", 89.99, 41),
        (5, "Tennis Racket", 119.99, 22),
        (5, "Water Bottle", 14.99, 156),
    ]

    cursor.executemany(
        "INSERT INTO products (category_id, name, price, stock_quantity) VALUES (?, ?, ?, ?)",
        products,
    )
    print(f"✓ Inserted {len(products)} products")

    # Generate orders and order items
    statuses = ["pending", "shipped", "delivered", "delivered", "delivered", "cancelled"]
    orders_data = []
    order_items_data = []

    base_date = datetime.now() - timedelta(days=90)

    for order_num in range(30):
        customer_id = random.randint(1, len(customers))
        order_date = base_date + timedelta(days=random.randint(0, 90))
        status = random.choice(statuses)

        # Create 1-4 items per order
        num_items = random.randint(1, 4)
        product_ids = random.sample(range(1, len(products) + 1), num_items)

        total_amount = 0
        for product_id in product_ids:
            quantity = random.randint(1, 3)
            # Get product price (approximate based on our data)
            unit_price = products[product_id - 1][2]
            total_amount += unit_price * quantity

            order_items_data.append((order_num + 1, product_id, quantity, unit_price))

        orders_data.append(
            (customer_id, order_date.isoformat(), status, round(total_amount, 2))
        )

    cursor.executemany(
        "INSERT INTO orders (customer_id, order_date, status, total_amount) VALUES (?, ?, ?, ?)",
        orders_data,
    )
    print(f"✓ Inserted {len(orders_data)} orders")

    cursor.executemany(
        "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
        order_items_data,
    )
    print(f"✓ Inserted {len(order_items_data)} order items")

    # Commit and close
    conn.commit()
    conn.close()

    print(f"\n✅ Playground database created successfully at {db_path}")
    print("\nDatabase statistics:")
    print(f"  - {len(customers)} customers")
    print(f"  - {len(categories)} categories")
    print(f"  - {len(products)} products")
    print(f"  - {len(orders_data)} orders")
    print(f"  - {len(order_items_data)} order items")
    print("\nRelationships:")
    print("  - customers → orders (1-to-many)")
    print("  - categories → products (1-to-many)")
    print("  - orders ↔ products (many-to-many via order_items)")


if __name__ == "__main__":
    create_playground_database()
