from flask import Flask, render_template, request, redirect, url_for, flash
from database import init_db, get_db, seed_menu, close_db
from data_structures import ChainedHashTable, OrderQueue
from algorithms import merge_sort, binary_search_by_id
from validation import validate_menu_item, validate_order

app = Flask(__name__)
app.secret_key = "change-this-development-secret"
app.teardown_appcontext(close_db)

# In-memory structures are rebuilt from the persistent SQLite database on demand.
def get_menu_cache():
    db = get_db()
    rows = db.execute("SELECT id, name, category, price, available FROM menu_items ORDER BY id").fetchall()
    items = [dict(row) for row in rows]
    table = ChainedHashTable()
    for item in items:
        table.insert(item["id"], item)
    return items, table

def get_order_queue():
    db = get_db()
    rows = db.execute(
        "SELECT id, customer_name, total, payment_method, payment_status, created_at "
        "FROM orders WHERE status = 'Pending' ORDER BY id"
    ).fetchall()
    queue = OrderQueue()
    for row in rows:
        queue.enqueue(dict(row))
    return queue

@app.route("/")
def index():
    db = get_db()
    menu_count = db.execute("SELECT COUNT(*) FROM menu_items").fetchone()[0]
    order_count = db.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    pending_count = db.execute("SELECT COUNT(*) FROM orders WHERE status='Pending'").fetchone()[0]
    recent_orders = db.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 5").fetchall()
    return render_template("index.html", menu_count=menu_count, order_count=order_count,
                           pending_count=pending_count, recent_orders=recent_orders)

@app.route("/menu", methods=["GET", "POST"])
def menu():
    db = get_db()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        price_text = request.form.get("price", "").strip()
        error = validate_menu_item(name, category, price_text)
        if error:
            flash(error, "error")
        else:
            try:
                db.execute("INSERT INTO menu_items(name, category, price, available) VALUES(?,?,?,1)",
                           (name, category, round(float(price_text), 2)))
                db.commit()
                flash("Menu item added successfully.", "success")
                return redirect(url_for("menu"))
            except Exception:
                db.rollback()
                flash("Could not add menu item. Check whether the item already exists.", "error")

    query = request.args.get("q", "").strip()
    sort_by = request.args.get("sort", "name")
    items, hash_table = get_menu_cache()
    if query:
        # Demonstrate custom hash-table lookup for numeric IDs; otherwise linear name search.
        if query.isdigit():
            found = hash_table.search(int(query))
            items = [found] if found else []
        else:
            items = [item for item in items if query.lower() in item["name"].lower()]
    if sort_by == "price":
        items = merge_sort(items, key="price")
    elif sort_by == "id":
        items = merge_sort(items, key="id")
    else:
        items = merge_sort(items, key="name")
    return render_template("menu.html", items=items, query=query, sort_by=sort_by)

@app.route("/menu/<int:item_id>/toggle", methods=["POST"])
def toggle_menu(item_id):
    db = get_db()
    row = db.execute("SELECT available FROM menu_items WHERE id=?", (item_id,)).fetchone()
    if not row:
        flash("Menu item not found.", "error")
    else:
        db.execute("UPDATE menu_items SET available=? WHERE id=?", (0 if row["available"] else 1, item_id))
        db.commit()
        flash("Menu availability updated.", "success")
    return redirect(url_for("menu"))

@app.route("/menu/<int:item_id>/delete", methods=["POST"])
def delete_menu(item_id):
    db = get_db()
    used = db.execute("SELECT 1 FROM order_items WHERE menu_item_id=? LIMIT 1", (item_id,)).fetchone()
    if used:
        flash("This item is linked to an order and cannot be deleted. Mark it unavailable instead.", "error")
    else:
        db.execute("DELETE FROM menu_items WHERE id=?", (item_id,))
        db.commit()
        flash("Menu item deleted.", "success")
    return redirect(url_for("menu"))

@app.route("/orders/new", methods=["GET", "POST"])
def new_order():
    db = get_db()
    available_items = db.execute("SELECT * FROM menu_items WHERE available=1 ORDER BY name").fetchall()
    if request.method == "POST":
        customer_name = request.form.get("customer_name", "").strip()
        payment_method = request.form.get("payment_method", "").strip()
        quantities = {}
        for key, value in request.form.items():
            if key.startswith("qty_"):
                try:
                    item_id = int(key[4:])
                    qty = int(value or "0")
                    if qty > 0:
                        quantities[item_id] = qty
                except ValueError:
                    pass
        error = validate_order(customer_name, payment_method, quantities)
        if error:
            flash(error, "error")
            return render_template("new_order.html", items=available_items)
        menu_rows = {}
        for item_id in quantities:
            row = db.execute("SELECT * FROM menu_items WHERE id=? AND available=1", (item_id,)).fetchone()
            if row:
                menu_rows[item_id] = row
        if len(menu_rows) != len(quantities):
            flash("One or more selected menu items are unavailable or missing.", "error")
            return render_template("new_order.html", items=available_items)
        total = sum(menu_rows[item_id]["price"] * qty for item_id, qty in quantities.items())
        payment_status = "Paid" if payment_method == "Cash" else "Awaiting GCash confirmation"
        try:
            cur = db.execute(
                "INSERT INTO orders(customer_name,total,payment_method,payment_status,status) VALUES(?,?,?,?,?)",
                (customer_name, round(total, 2), payment_method, payment_status, "Pending"))
            order_id = cur.lastrowid
            for item_id, qty in quantities.items():
                row = menu_rows[item_id]
                db.execute("INSERT INTO order_items(order_id,menu_item_id,item_name,unit_price,quantity,line_total) VALUES(?,?,?,?,?,?)",
                           (order_id, item_id, row["name"], row["price"], qty, round(row["price"] * qty, 2)))
            db.commit()
            flash(f"Order #{order_id} created. Total: ₱{total:.2f}", "success")
            return redirect(url_for("order_detail", order_id=order_id))
        except Exception:
            db.rollback()
            flash("Order could not be saved. Please try again.", "error")
    return render_template("new_order.html", items=available_items)

@app.route("/orders")
def orders():
    db = get_db()
    status = request.args.get("status", "").strip()
    sql = "SELECT * FROM orders"
    params = []
    if status in ("Pending", "Completed", "Cancelled"):
        sql += " WHERE status=?"
        params.append(status)
    sql += " ORDER BY id DESC"
    all_orders = db.execute(sql, params).fetchall()
    queue = get_order_queue()
    pending_ids = set()
    while not queue.is_empty():
        pending_ids.add(queue.dequeue()["id"])
    return render_template("orders.html", orders=all_orders, status=status, pending_ids=pending_ids)

@app.route("/orders/<int:order_id>")
def order_detail(order_id):
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    if not order:
        flash("Order not found.", "error")
        return redirect(url_for("orders"))
    items = db.execute("SELECT * FROM order_items WHERE order_id=? ORDER BY id", (order_id,)).fetchall()
    return render_template("order_detail.html", order=order, items=items)

@app.route("/orders/<int:order_id>/complete", methods=["POST"])
def complete_order(order_id):
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    if not order:
        flash("Order not found.", "error")
    elif order["status"] != "Pending":
        flash("Only pending orders can be completed.", "error")
    else:
        db.execute("UPDATE orders SET status='Completed' WHERE id=?", (order_id,))
        db.commit()
        flash(f"Order #{order_id} marked completed.", "success")
    return redirect(url_for("orders"))

@app.route("/orders/<int:order_id>/cancel", methods=["POST"])
def cancel_order(order_id):
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    if not order:
        flash("Order not found.", "error")
    elif order["status"] != "Pending":
        flash("Only pending orders can be cancelled.", "error")
    else:
        db.execute("UPDATE orders SET status='Cancelled' WHERE id=?", (order_id,))
        db.commit()
        flash(f"Order #{order_id} cancelled.", "success")
    return redirect(url_for("orders"))

@app.route("/reports")
def reports():
    db = get_db()
    totals = db.execute("SELECT COUNT(*) AS count, COALESCE(SUM(total),0) AS revenue FROM orders WHERE status='Completed'").fetchone()
    bestsellers = db.execute("""
        SELECT item_name, SUM(quantity) AS qty
        FROM order_items JOIN orders ON orders.id=order_items.order_id
        WHERE orders.status='Completed'
        GROUP BY item_name ORDER BY qty DESC, item_name LIMIT 5
    """).fetchall()
    return render_template("reports.html", totals=totals, bestsellers=bestsellers)

@app.route("/search-binary")

def search_binary():
    query = request.args.get("id", "").strip()
    result = None
    error = None

    if query:
        if not query.isdigit():
            error = "Enter a numeric menu item ID."
        else:
            items, _ = get_menu_cache()
            sorted_items = merge_sort(items, key="id")
            result = binary_search_by_id(sorted_items, int(query))

            if result is None:
                error = f"No menu item found with ID {query}."

    return render_template(
        "binary_search.html",
        query=query,
        result=result,
        error=error
    )


@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404

with app.app_context():
    init_db()
    seed_menu()

if __name__ == "__main__":
    app.run(debug=True)
