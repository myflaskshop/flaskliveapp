from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        product TEXT,
        quantity INTEGER,
        address TEXT,
        payment TEXT,
        delivery_time TEXT,
        total_price INTEGER,
        order_date TEXT,
        status TEXT DEFAULT 'Pending'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        message TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- PRODUCTS ----------------
products = [
    {"name": "Chicken", "price": 300, "image": "chicken.jpg"},
    {"name": "Mutton", "price": 800, "image": "mutton.jpg"},
    {"name": "Eggs", "price": 6, "image": "eggs.jpg"}
]

# ---------------- SUBCATEGORIES ----------------
categories = {
    "Chicken": [
        {"name": "Breast", "price": 150, "image": "chicken_breast.jpg"},
        {"name": "Leg Piece", "price": 200, "image": "chicken_leg.jpg"},
        {"name": "Masala", "price": 70, "image": "chicken_masala.jpg"}
    ],
    "Mutton": [
        {"name": "Leg", "price": 500, "image": "mutton_leg.jpg"},
        {"name": "Shoulder", "price": 400, "image": "mutton_shoulder.jpg"},
        {"name": "Masala", "price": 80, "image": "mutton_masala.jpg"},
        {"name": "mundi", "price": 600, "image": "mundi.jpg"},
        {"name": "chap", "price": 400, "image": "motton_chap.jpg"}
    ],
    "Eggs": [
        
        {"name": "Brown", "price": 8, "image": "egg_Brown.jpg"},
        
    ]
}

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html", products=products)

# ---------------- CATEGORY PAGE ----------------
@app.route("/category/<product_name>")
def category(product_name):
    subcategories = categories.get(product_name, [])
    return render_template("category.html", product_name=product_name, subcategories=subcategories)

# ---------------- ORDER FORM (MULTI-STEP) ----------------
@app.route("/order_form/<product>/<subcategory>", methods=["GET", "POST"])
def order_form(product, subcategory):
    # Get price of selected subcategory
    subcat_list = categories.get(product, [])
    unit_price = next((item['price'] for item in subcat_list if item['name'] == subcategory), 0)

    if request.method == "POST":
        name = request.form.get("name")
        phone = request.form.get("phone")
        address = request.form.get("address")
        quantity = int(request.form.get("quantity"))
        payment = request.form.get("payment")
        delivery_time = request.form.get("delivery_time")

        total_price = unit_price * quantity
        order_date = datetime.now().strftime("%Y-%m-%d %H:%M")

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO orders (name, phone, product, quantity, address, payment, delivery_time, total_price, order_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, phone, f"{product} - {subcategory}", quantity, address, payment, delivery_time, total_price, order_date))
        order_id = cursor.lastrowid
        conn.commit()
        conn.close()

        order = {
            "id": order_id,
            "name": name,
            "phone": phone,
            "product": product,
            "subcategory": subcategory,
            "quantity": quantity,
            "address": address,
            "payment": payment,
            "delivery_time": delivery_time,
            "total_price": total_price,
            "status": "Pending"
        }

        return render_template("success.html", order=order, order_unit_price=unit_price)

    return render_template("order_form.html", product=product, subcategory=subcategory, unit_price=unit_price)

# ---------------- CANCEL ORDER ----------------
@app.route("/cancel_order/<int:order_id>")
def cancel_order(order_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status='Cancelled' WHERE id=?", (order_id,))
    conn.commit()
    cursor.execute("SELECT * FROM orders WHERE id=?", (order_id,))
    data = cursor.fetchone()
    conn.close()

    order = {
        "id": data[0],
        "name": data[1],
        "phone": data[2],
        "product": data[3],
        "quantity": data[4],
        "address": data[5],
        "payment": data[6],
        "delivery_time": data[7],
        "total_price": data[8],
        "status": data[10]
    }

    # Get unit price from products or subcategories
    base_name = order['product'].split(" - ")[0]
    sub_name = order['product'].split(" - ")[1] if " - " in order['product'] else ""
    subcat_list = categories.get(base_name, [])
    unit_price = next((item['price'] for item in subcat_list if item['name'] == sub_name), 0)

    return render_template("success.html", order=order, order_unit_price=unit_price)

# ---------------- COMPLETE ORDER ----------------
@app.route("/complete_order/<int:order_id>")
def complete_order(order_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status='Completed' WHERE id=?", (order_id,))
    conn.commit()
    cursor.execute("SELECT * FROM orders WHERE id=?", (order_id,))
    data = cursor.fetchone()
    conn.close()

    order = {
        "id": data[0],
        "name": data[1],
        "phone": data[2],
        "product": data[3],
        "quantity": data[4],
        "address": data[5],
        "payment": data[6],
        "delivery_time": data[7],
        "total_price": data[8],
        "status": "Completed"
    }

    # Get unit price
    base_name = order['product'].split(" - ")[0]
    sub_name = order['product'].split(" - ")[1] if " - " in order['product'] else ""
    subcat_list = categories.get(base_name, [])
    unit_price = next((item['price'] for item in subcat_list if item['name'] == sub_name), 0)

    return render_template("success.html", order=order, order_unit_price=unit_price, completed=True)

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("username") == "admin" and request.form.get("password") == "1234":
            session["admin"] = True
            return redirect("/admin")
        else:
            return render_template("login.html", error="Invalid login")
    return render_template("login.html")

# ---------------- ADMIN ----------------
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders")
    orders = cursor.fetchall()
    conn.close()
    return render_template("admin.html", orders=orders)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/")

# ---------------- FEEDBACK ----------------
@app.route("/feedback", methods=["POST"])
def feedback():
    name = request.form.get("name")
    message = request.form.get("message")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO feedback (name, message) VALUES (?, ?)", (name, message))
    conn.commit()
    conn.close()
    return redirect("/")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
