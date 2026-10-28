
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "inventory-dev-key")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Use the Docker volume path when configured; otherwise use the project folder.
DB_PATH = os.environ.get(
    "DB_PATH",
    os.path.join(BASE_DIR, "inventory.db")
)


def get_db():
    # Ensure the database directory exists.
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                min_stock INTEGER NOT NULL DEFAULT 5
            )
        """)


# Create the table when Flask or Gunicorn loads the application.
initialize_db()


@app.route("/")
def index():
    with get_db() as conn:
        total_products = conn.execute(
            "SELECT COUNT(*) FROM products"
        ).fetchone()[0]

        total_stock = conn.execute(
            "SELECT COALESCE(SUM(quantity), 0) FROM products"
        ).fetchone()[0]

        low_stock = conn.execute(
            "SELECT COUNT(*) FROM products WHERE quantity <= min_stock"
        ).fetchone()[0]

        products = conn.execute(
            "SELECT * FROM products ORDER BY id DESC LIMIT 5"
        ).fetchall()

    return render_template(
        "index.html",
        total_products=total_products,
        total_stock=total_stock,
        low_stock=low_stock,
        products=products
    )


@app.route("/products")
def product_list():
    with get_db() as conn:
        products = conn.execute(
            "SELECT * FROM products ORDER BY id DESC"
        ).fetchall()

    return render_template(
        "products.html",
        products=products
    )


@app.route("/add", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()

        try:
            quantity = int(request.form.get("quantity", "0"))
            price = float(request.form.get("price", "0"))
            min_stock = int(request.form.get("min_stock", "5"))

            if not name or not category:
                raise ValueError(
                    "Enter the product name and category."
                )

            if quantity < 0 or price < 0 or min_stock < 0:
                raise ValueError(
                    "Numbers cannot be negative."
                )

        except ValueError as error:
            flash(str(error) or "Enter valid numbers.")
            return redirect(url_for("add_product"))

        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO products
                (name, category, quantity, price, min_stock)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, category, quantity, price, min_stock)
            )

        flash("Product added successfully!")
        return redirect(url_for("product_list"))

    return render_template("add_product.html")


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
