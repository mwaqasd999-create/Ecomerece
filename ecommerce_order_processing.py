"""E-Commerce Order Processing System assessment.

Uses only Python's standard library and keeps data in memory.
"""
from decimal import Decimal, ROUND_HALF_UP


def money(value):
    """Convert a number to a two-decimal Decimal using half-up rounding."""
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


products = {
    "P001": {"name": "Laptop", "price": Decimal("1200.00"), "category": "Electronics", "stock": 10},
    "P002": {"name": "Mouse", "price": Decimal("25.00"), "category": "Accessories", "stock": 50},
    "P003": {"name": "Keyboard", "price": Decimal("75.00"), "category": "Accessories", "stock": 20},
    "P004": {"name": "Monitor", "price": Decimal("300.00"), "category": "Electronics", "stock": 15},
}

orders = [
    {
        "order_id": "ORD001",
        "customer": "Ali",
        "items": [
            {"product_id": "P001", "quantity": 1},
            {"product_id": "P002", "quantity": 2},
        ],
        "payment_status": "paid",
    },
    {
        "order_id": "ORD002",
        "customer": "Ahmed",
        "items": [
            {"product_id": "P003", "quantity": 2},
            {"product_id": "P004", "quantity": 1},
        ],
        "payment_status": "paid",
    },
    {
        "order_id": "ORD003",
        "customer": "Ali",
        "items": [{"product_id": "P002", "quantity": 5}],
        "payment_status": "pending",
    },
]

LEGB_GLOBAL_LABEL = "global scope"
LOW_STOCK_THRESHOLD = 5
CENT = Decimal("0.01")


def demonstrate_legb_scope():
    """Show Local, Enclosing, Global and Built-in scope in one example."""
    enclosing_label = "enclosing scope"

    def inner_function():
        local_label = "local scope"
        return {
            "local": local_label,
            "enclosing": enclosing_label,
            "global": LEGB_GLOBAL_LABEL,
            "built_in_length": len(enclosing_label),
        }

    return inner_function()


def sum_amounts(*amounts):
    """Add any number of money amounts (uses *args) and return a Decimal."""
    total = Decimal("0.00")
    for amount in amounts:
        total += money(amount)
    return money(total)


def calculate_order_subtotal(order, product_catalog):
    """Return price x quantity summed over all items; unknown products are skipped."""
    line_totals = [
        money(product_catalog[item["product_id"]]["price"]) * item["quantity"]
        for item in order.get("items", [])
        if item.get("product_id") in product_catalog
    ]
    return sum_amounts(*line_totals)


def calculate_discount(subtotal):
    """Return the discount: 15% from 1000, 10% from 500, 5% from 200, else 0."""
    subtotal = money(subtotal)
    if subtotal >= Decimal("1000.00"):
        rate = Decimal("0.15")
    elif subtotal >= Decimal("500.00"):
        rate = Decimal("0.10")
    elif subtotal >= Decimal("200.00"):
        rate = Decimal("0.05")
    else:
        rate = Decimal("0.00")
    return money(subtotal * rate)


def calculate_shipping(subtotal):
    """Return shipping: free from 500, otherwise 20."""
    return Decimal("0.00") if money(subtotal) >= Decimal("500.00") else Decimal("20.00")


def make_result(order, status, message, subtotal=0, discount=0, shipping=0, total=0, items=None):
    """Build the result record returned for every processed order."""
    order = order if isinstance(order, dict) else {}
    raw_order_id = order.get("order_id", "Unknown")
    order_id = raw_order_id.strip().upper() if isinstance(raw_order_id, str) else "Unknown"
    raw_customer = order.get("customer", "Unknown")
    customer = raw_customer.strip() if isinstance(raw_customer, str) else "Unknown"
    return {
        "order_id": order_id,
        "customer": customer,
        "status": status,
        "message": message,
        "subtotal": money(subtotal),
        "discount": money(discount),
        "shipping": money(shipping),
        "total": money(total),
        "items": items if items is not None else [],
    }


def validate_order(order, product_catalog):
    """Return (True, message) for a valid order or (False, reason) otherwise."""
    if not isinstance(order, dict):
        return False, "Invalid order format."

    order_id = order.get("order_id")
    if not isinstance(order_id, str) or not order_id.strip():
        return False, "Missing or invalid order ID."

    customer = order.get("customer")
    if not isinstance(customer, str) or not customer.strip():
        return False, "Missing or invalid customer."

    if not isinstance(product_catalog, dict) or not product_catalog:
        return False, "No products available."

    items = order.get("items")
    if not isinstance(items, list) or not items:
        return False, "Order has no items."

    if order.get("payment_status") not in ("paid", "pending"):
        return False, "Invalid payment status."

    requested = {}
    for item in items:
        if not isinstance(item, dict):
            return False, "Invalid item format."

        product_id = item.get("product_id")
        quantity = item.get("quantity")
        if not isinstance(product_id, str) or product_id not in product_catalog:
            return False, "Product ID does not exist."

        product = product_catalog[product_id]
        if not isinstance(product, dict):
            return False, "Invalid product data."

        price = product.get("price")
        stock = product.get("stock")
        try:
            valid_price = isinstance(price, (int, float, Decimal)) and not isinstance(price, bool) and money(price) >= 0
        except (ValueError, TypeError, ArithmeticError):
            valid_price = False
        if (
            not valid_price
            or not isinstance(stock, int)
            or isinstance(stock, bool)
            or stock < 0
        ):
            return False, "Invalid product price or stock."

        if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
            return False, "Quantity must be a positive integer."

        requested[product_id] = requested.get(product_id, 0) + quantity

    for product_id, quantity in requested.items():
        if quantity > product_catalog[product_id]["stock"]:
            return False, "Insufficient stock."

    return True, "Order is valid."


def process_order(order, product_catalog, *items_to_process,
                  processed_order_ids=None, **options):
    """Process an order; extra positional item dictionaries demonstrate *args.

    Accepted keyword options are include_shipping and apply_discount. Pending
    orders receive a quote but do not deduct stock.
    """
    allowed_options = {"include_shipping", "apply_discount"}
    unknown_options = set(options) - allowed_options
    if unknown_options:
        return make_result(
            order, "rejected",
            "Unknown option(s): " + ", ".join(sorted(unknown_options)) + ".",
        )

    include_shipping = options.get("include_shipping", True)
    apply_discount = options.get("apply_discount", True)
    if not isinstance(include_shipping, bool) or not isinstance(apply_discount, bool):
        return make_result(order, "rejected", "Options must be True or False.")

    if not isinstance(order, dict):
        return make_result(order, "rejected", "Invalid order format.")

    selected_order = order.copy()
    raw_order_id = selected_order.get("order_id")
    if isinstance(raw_order_id, str):
        selected_order["order_id"] = raw_order_id.strip().upper()
    raw_customer = selected_order.get("customer")
    if isinstance(raw_customer, str):
        selected_order["customer"] = raw_customer.strip()

    original_items = selected_order.get("items")
    if items_to_process:
        if not isinstance(original_items, list):
            return make_result(selected_order, "rejected", "Order has no items.")
        selected_order["items"] = original_items + list(items_to_process)

    order_id = selected_order.get("order_id")
    if processed_order_ids is not None and order_id in processed_order_ids:
        return make_result(selected_order, "rejected", "Duplicate order ID.")

    valid, message = validate_order(selected_order, product_catalog)
    if not valid:
        return make_result(selected_order, "rejected", message)

    if processed_order_ids is not None:
        processed_order_ids.add(order_id)

    processed_items = []
    for item in selected_order["items"]:
        product_id = item["product_id"]
        product = product_catalog[product_id]
        quantity = item["quantity"]
        unit_price = money(product["price"])
        line_total = money(unit_price * quantity)
        processed_items.append({
            "product_id": product_id,
            "name": product.get("name") or product_id,
            "quantity": quantity,
            "unit_price": unit_price,
            "line_total": line_total,
        })

    subtotal = calculate_order_subtotal(selected_order, product_catalog)
    discount = calculate_discount(subtotal) if apply_discount else Decimal("0.00")
    shipping = calculate_shipping(subtotal) if include_shipping else Decimal("0.00")
    total = money(subtotal - discount + shipping)

    if selected_order["payment_status"] == "pending":
        return make_result(
            selected_order, "pending",
            "Payment is pending. Order not completed.",
            subtotal, discount, shipping, total, processed_items,
        )

    for item in processed_items:
        product_catalog[item["product_id"]]["stock"] -= item["quantity"]

    return make_result(
        selected_order, "paid", "Order processed successfully.",
        subtotal, discount, shipping, total, processed_items,
    )


def generate_customer_report(processed_orders):
    """Return customer spending grouped without case/whitespace differences."""
    customer_totals = {}
    display_names = {}
    for order in processed_orders:
        if order.get("status") != "paid":
            continue
        raw_customer = order.get("customer")
        if not isinstance(raw_customer, str) or not raw_customer.strip():
            continue
        customer = raw_customer.strip()
        key = customer.casefold()
        display_names.setdefault(key, customer)
        customer_totals[key] = money(customer_totals.get(key, Decimal("0.00")) + money(order.get("total", 0)))

    display_totals = {display_names[key]: value for key, value in customer_totals.items()}
    if not customer_totals:
        return {"top_customer": "None", "customer_totals": {}}

    highest_total = max(customer_totals.values())
    tied_keys = sorted(key for key, value in customer_totals.items() if value == highest_total)
    return {
        "top_customer": ", ".join(display_names[key] for key in tied_keys),
        "customer_totals": display_totals,
    }


def generate_product_report(processed_orders, product_catalog, low_stock_threshold=LOW_STOCK_THRESHOLD):
    """Return top-selling product(s), low-stock products and categories."""
    product_sales = {}
    for order in processed_orders:
        if order.get("status") != "paid":
            continue
        items = order.get("items", [])
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            product_id = item.get("product_id")
            quantity = item.get("quantity")
            if isinstance(product_id, str) and isinstance(quantity, int) and not isinstance(quantity, bool):
                product_sales[product_id] = product_sales.get(product_id, 0) + quantity

    def product_name(product_id):
        product = product_catalog.get(product_id, {})
        if not isinstance(product, dict):
            return product_id
        return product.get("name") or product_id

    if product_sales:
        highest_quantity = max(product_sales.values())
        top_ids = sorted(
            (product_id for product_id, quantity in product_sales.items() if quantity == highest_quantity),
            key=lambda product_id: product_name(product_id).casefold(),
        )
        top_product = ", ".join(product_name(product_id) for product_id in top_ids)
    else:
        top_product = "None"

    low_stock_products = []
    categories = set()
    for product_id, product in product_catalog.items():
        if not isinstance(product, dict):
            continue
        stock = product.get("stock")
        if isinstance(stock, int) and not isinstance(stock, bool) and stock < low_stock_threshold:
            low_stock_products.append(product.get("name") or product_id)
        category = product.get("category")
        if isinstance(category, str) and category:
            categories.add(category)

    return {
        "top_selling_product": top_product,
        "product_sales": product_sales,
        "low_stock_products": low_stock_products,
        "categories": categories,
    }


def build_sales_summary(processed_orders, product_catalog, low_stock_threshold=LOW_STOCK_THRESHOLD):
    """Build a testable sales summary without printing it."""
    customer_report = generate_customer_report(processed_orders)
    product_report = generate_product_report(processed_orders, product_catalog, low_stock_threshold)
    paid = [order for order in processed_orders if order.get("status") == "paid"]
    return {
        "total_orders": len(processed_orders),
        "paid_orders": len(paid),
        "pending_orders": sum(order.get("status") == "pending" for order in processed_orders),
        "rejected_orders": sum(order.get("status") == "rejected" for order in processed_orders),
        "unique_paying_customers": len({
            order.get("customer", "").strip().casefold()
            for order in paid
            if isinstance(order.get("customer"), str) and order.get("customer", "").strip()
        }),
        "total_revenue": sum_amounts(*[order.get("total", 0) for order in paid]),
        "total_discount": sum_amounts(*[order.get("discount", 0) for order in paid]),
        "total_shipping": sum_amounts(*[order.get("shipping", 0) for order in paid]),
        "top_customer": customer_report["top_customer"],
        "top_selling_product": product_report["top_selling_product"],
        "low_stock_products": product_report["low_stock_products"],
    }


def print_sales_report(summary):
    """Print a sales summary in the format required by the assignment."""
    print("\n========== SALES REPORT ==========\n")
    print(f"Total Orders: {summary['total_orders']}")
    print(f"Paid Orders: {summary['paid_orders']}")
    print(f"Pending Orders: {summary['pending_orders']}")
    print(f"Rejected Orders: {summary['rejected_orders']}\n")
    print(f"Total Revenue: ${summary['total_revenue']:.2f}")
    print(f"Total Discount: ${summary['total_discount']:.2f}")
    print(f"Total Shipping: ${summary['total_shipping']:.2f}\n")
    print(f"Top Customer: {summary['top_customer']}")
    print(f"Top Selling Product: {summary['top_selling_product']}\n")
    print("Low Stock Products:")
    if summary["low_stock_products"]:
        for product in summary["low_stock_products"]:
            print(f"- {product}")
    else:
        print("- None")
    print("\n==================================")


def generate_sales_report(processed_orders, product_catalog):
    """Backward-compatible report helper: build and print the summary."""
    summary = build_sales_summary(processed_orders, product_catalog)
    print_sales_report(summary)
    return summary


def process_all_orders(order_list, product_catalog, **options):
    """Process a batch, forwarding valid processing options to each order."""
    processed_orders = []
    processed_ids = set()
    for order in order_list:
        result = process_order(
            order,
            product_catalog,
            processed_order_ids=processed_ids,
            **options,
        )
        processed_orders.append(result)
        print(f"{result['order_id']}: {result['message']}")
    return processed_orders


def main():
    processed_orders = process_all_orders(orders, products)
    summary = build_sales_summary(processed_orders, products)
    print_sales_report(summary)
    print("\nRemaining Inventory:")
    for product_id, product in products.items():
        print(f"{product_id} - {product.get('name') or product_id}: {product.get('stock', 'Unknown')}")
    print("\nLEGB demonstration:", demonstrate_legb_scope())


if __name__ == "__main__":
    main()
