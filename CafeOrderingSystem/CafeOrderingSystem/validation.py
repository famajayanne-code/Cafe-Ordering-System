def validate_menu_item(name, category, price_text):
    if not name:
        return "Item name is required."
    if len(name) > 80:
        return "Item name must be 80 characters or fewer."
    if not category:
        return "Category is required."
    try:
        price = float(price_text)
    except (TypeError, ValueError):
        return "Enter a valid price."
    if price < 0:
        return "Price cannot be negative."
    if price > 100000:
        return "Price is too high."
    return None

def validate_order(customer_name, payment_method, quantities):
    if not customer_name:
        return "Customer name is required."
    if len(customer_name) > 100:
        return "Customer name must be 100 characters or fewer."
    if payment_method not in ("Cash", "GCash"):
        return "Choose Cash or GCash as the payment method."
    if not quantities:
        return "Select at least one menu item and enter a quantity."
    if any(not isinstance(qty, int) or qty <= 0 for qty in quantities.values()):
        return "Quantities must be positive whole numbers."
    return None
