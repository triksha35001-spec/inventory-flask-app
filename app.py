from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"   # login ke liye required

# ---------- DATABASE ----------
def get_db_connection():
    conn = sqlite3.connect("inventory.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------- CREATE TABLE ----------
conn = get_db_connection()
conn.execute("""
CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    quantity INTEGER,
    price REAL
)
""")
conn.close()

# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            session["user"] = "admin"
            return redirect("/")
        else:
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

# ---------- HOME + ADD + SEARCH ----------
@app.route("/", methods=["GET", "POST"])
def index():
    if "user" not in session:
        return redirect("/login")

    conn = get_db_connection()

    # ADD ITEM
    if request.method == "POST":
        name = request.form["name"].strip()
        quantity = int(request.form["quantity"])
        price = float(request.form["price"])

        try:
            conn.execute(
                "INSERT INTO inventory (name, quantity, price) VALUES (?, ?, ?)",
                (name, quantity, price)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.execute(
                "UPDATE inventory SET quantity = quantity + ?, price = ? WHERE name = ?",
                (quantity, price, name)
            )
            conn.commit()

        conn.close()
        return redirect("/")

    # SEARCH
    search = request.args.get("search", "")
    if search:
        items = conn.execute(
            "SELECT * FROM inventory WHERE name LIKE ?",
            (f"%{search}%",)
        ).fetchall()
    else:
        items = conn.execute("SELECT * FROM inventory").fetchall()

    conn.close()
    return render_template("index.html", inventory=items)

# ---------- UPDATE ----------
@app.route("/update/<int:id>", methods=["POST"])
def update(id):
    if "user" not in session:
        return redirect("/login")

    quantity = int(request.form["quantity"])
    price = float(request.form["price"])

    conn = get_db_connection()
    conn.execute(
        "UPDATE inventory SET quantity = ?, price = ? WHERE id = ?",
        (quantity, price, id)
    )
    conn.commit()
    conn.close()

    return redirect("/")

# ---------- DELETE ----------
@app.route("/delete/<int:id>")
def delete(id):
    if "user" not in session:
        return redirect("/login")

    conn = get_db_connection()
    conn.execute("DELETE FROM inventory WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return redirect("/")

# ---------- RUN APP (UPDATED LINE) ----------
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
