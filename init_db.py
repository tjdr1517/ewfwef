import sqlite3

conn = sqlite3.connect('menu.db')
cur = conn.cursor()

# Drop existing tables if they exist
cur.execute("DROP TABLE IF EXISTS menu")
cur.execute("DROP TABLE IF EXISTS orders")
cur.execute("DROP TABLE IF EXISTS order_items")

# Create menu table with stock
cur.execute("""
CREATE TABLE menu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price INTEGER NOT NULL,
    image_url TEXT,
    stock INTEGER NOT NULL DEFAULT 100
)
""")

# Create orders table
cur.execute("""
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_number TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT '접수'
)
""")

# Create order_items table
cur.execute("""
CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    menu_id INTEGER,
    quantity INTEGER NOT NULL,
    FOREIGN KEY(order_id) REFERENCES orders(id),
    FOREIGN KEY(menu_id) REFERENCES menu(id)
)
""")

# Insert sample menu items
cur.execute("INSERT INTO menu (name, price, image_url, stock) VALUES (?, ?, ?, ?)", ('아메리카노', 4000, '/static/images/americano.jpg', 100))
cur.execute("INSERT INTO menu (name, price, image_url, stock) VALUES (?, ?, ?, ?)", ('카페라떼', 4500, '/static/images/cafelatte.jpg', 100))
cur.execute("INSERT INTO menu (name, price, image_url, stock) VALUES (?, ?, ?, ?)", ('카푸치노', 4500, '/static/images/cappuccino.jpg', 50))
cur.execute("INSERT INTO menu (name, price, image_url, stock) VALUES (?, ?, ?, ?)", ('치즈케이크', 6000, '/static/images/cheesecake.jpg', 20))

conn.commit()
conn.close()

print("Database initialized successfully.")