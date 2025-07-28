from flask import Flask, render_template, request, jsonify, session, redirect, url_for, abort, Response
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import csv
from io import StringIO

app = Flask(__name__)
app.secret_key = 'supersecretkey123'  # Change this in production!

# -------------------- LOGIN REQUIRED DECORATOR --------------------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# -------------------- ROLE REQUIRED DECORATOR --------------------
def role_required(role):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            user_role = session.get('user_role')
            if user_role != role:
                return abort(403, description="Access denied")
            return f(*args, **kwargs)
        return wrapped
    return decorator

# -------------------- DATABASE INIT --------------------
def init_db():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    # Products table with currency and unit_type
    cur.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        stock REAL NOT NULL,
        barcode TEXT UNIQUE,
        currency TEXT DEFAULT 'LBP',
        unit_type TEXT DEFAULT 'piece'
    )''')

    # Sales table
    cur.execute('''CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        quantity REAL NOT NULL,
        total_price REAL NOT NULL,
        sale_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(product_id) REFERENCES products(id)
    )''')

    # Users table with role column
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'cashier'
    )''')

    conn.commit()
    conn.close()

init_db()

# -------------------- ROUTES --------------------

@app.route('/')
@login_required
def index():
    return render_template('index.html', role=session.get('user_role'))

@app.route('/sales')
@login_required
def sales_page():
    return render_template('sales.html', role=session.get('user_role'))

@app.route('/products', methods=['GET'])
@login_required
def get_products():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("SELECT id, name, price, stock, barcode, currency, unit_type FROM products")
    products = cur.fetchall()
    conn.close()
    # Return as list of dicts for clarity
    keys = ['id', 'name', 'price', 'stock', 'barcode', 'currency', 'unit_type']
    products_list = [dict(zip(keys, p)) for p in products]
    return jsonify(products_list)

@app.route('/products-by-barcode/<barcode>', methods=['GET'])
@login_required
def get_product_by_barcode(barcode):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("SELECT id, name, price, stock, barcode, currency, unit_type FROM products WHERE barcode = ?", (barcode,))
    product = cur.fetchone()
    conn.close()

    if product:
        keys = ['id', 'name', 'price', 'stock', 'barcode', 'currency', 'unit_type']
        return jsonify(dict(zip(keys, product)))
    return jsonify({})

@app.route('/sell', methods=['POST'])
@login_required
def sell_product():
    data = request.get_json()
    barcode = data.get('barcode')
    quantity = float(data.get('quantity'))  # allow float for weight

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    # Find product
    cur.execute("SELECT id, stock, price, name FROM products WHERE barcode = ?", (barcode,))
    product = cur.fetchone()

    if not product:
        conn.close()
        return jsonify({'error': 'Product not found'}), 404

    product_id, stock, price, name = product

    if stock < quantity:
        conn.close()
        return jsonify({'error': 'Not enough stock'}), 400

    total_price = price * quantity

    # Update stock and record sale
    cur.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (quantity, product_id))
    cur.execute("INSERT INTO sales (product_id, quantity, total_price) VALUES (?, ?, ?)",
                (product_id, quantity, total_price))

    conn.commit()
    conn.close()

    # Return JSON for receipt display
    return jsonify({
        'message': 'Sale successful',
        'product': name,
        'quantity': quantity,
        'price': price,
        'total': total_price
    })

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("SELECT id, password, role FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            session['user_role'] = user[2]  # Store role in session
            return redirect('/')
        return "Invalid credentials", 401

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/api/sales')
@login_required
def api_sales():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute('''
        SELECT s.quantity, s.total_price, s.sale_time, p.name
        FROM sales s
        JOIN products p ON s.product_id = p.id
        ORDER BY s.sale_time DESC
    ''')
    data = cur.fetchall()
    conn.close()

    sales = [{
        'product_name': row[3],
        'quantity': row[0],
        'total_price': row[1],
        'sale_time': row[2]
    } for row in data]

    return jsonify(sales)

# -------------------- PRODUCT MANAGEMENT (ADMIN ONLY) --------------------

@app.route('/manage-products')
@login_required
@role_required('admin')
def manage_products_page():
    return render_template('products.html', role=session.get('user_role'))

@app.route('/products', methods=['POST'])
@login_required
@role_required('admin')
def create_product():
    data = request.get_json()
    name = data.get('name')
    price = float(data.get('price'))
    stock = float(data.get('stock'))  # float to allow weight in kg
    barcode = data.get('barcode')
    currency = data.get('currency', 'LBP')
    unit_type = data.get('unit_type', 'piece')

    if not all([name, price, stock, barcode, currency, unit_type]):
        return jsonify({'error': 'Missing product data'}), 400

    try:
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO products (name, price, stock, barcode, currency, unit_type) VALUES (?, ?, ?, ?, ?, ?)",
            (name, price, stock, barcode, currency, unit_type)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Barcode must be unique'}), 400

    conn.close()
    return jsonify({'message': 'Product created'}), 201

@app.route('/products/<int:product_id>', methods=['PUT'])
@login_required
@role_required('admin')
def update_product(product_id):
    data = request.get_json()
    name = data.get('name')
    price = float(data.get('price'))
    stock = float(data.get('stock'))
    barcode = data.get('barcode')
    currency = data.get('currency', 'LBP')
    unit_type = data.get('unit_type', 'piece')

    if not all([name, price, stock, barcode, currency, unit_type]):
        return jsonify({'error': 'Missing product data'}), 400

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    # Check if product exists
    cur.execute("SELECT id FROM products WHERE id = ?", (product_id,))
    if not cur.fetchone():
        conn.close()
        return jsonify({'error': 'Product not found'}), 404

    # Check if barcode is unique for other products
    cur.execute("SELECT id FROM products WHERE barcode = ? AND id != ?", (barcode, product_id))
    if cur.fetchone():
        conn.close()
        return jsonify({'error': 'Barcode already used by another product'}), 400

    cur.execute(
        "UPDATE products SET name = ?, price = ?, stock = ?, barcode = ?, currency = ?, unit_type = ? WHERE id = ?",
        (name, price, stock, barcode, currency, unit_type, product_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'message': 'Product updated'})

@app.route('/products/<int:product_id>', methods=['DELETE'])
@login_required
@role_required('admin')
def delete_product(product_id):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    # Check if product exists
    cur.execute("SELECT id FROM products WHERE id = ?", (product_id,))
    if not cur.fetchone():
        conn.close()
        return jsonify({'error': 'Product not found'}), 404

    # Delete product
    cur.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Product deleted'})

# -------------------- EXPORT SALES CSV --------------------
@app.route('/export-sales')
@login_required
def export_sales():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute('''
        SELECT p.name, s.quantity, s.total_price, s.sale_time
        FROM sales s
        JOIN products p ON s.product_id = p.id
        ORDER BY s.sale_time DESC
    ''')
    data = cur.fetchall()
    conn.close()

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['Product', 'Quantity', 'Total Price (LBP)', 'Sale Time'])
    writer.writerows(data)

    output = si.getvalue()
    si.close()

    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=sales_export.csv'}
    )

# -------------------- START SERVER --------------------
if __name__ == '__main__':
    app.run(debug=True)
