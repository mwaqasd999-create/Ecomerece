import copy
import unittest
from decimal import Decimal

import ecommerce_order_processing as app


def fresh_products():
    return {
        "P001": {"name": "Laptop", "price": Decimal("1200.00"), "category": "Electronics", "stock": 2},
        "P002": {"name": "Mouse", "price": Decimal("25.00"), "category": "Accessories", "stock": 10},
    }


def make_order(order_id="T001", customer="Test", items=None, payment_status="paid"):
    return {
        "order_id": order_id,
        "customer": customer,
        "items": items if items is not None else [{"product_id": "P002", "quantity": 1}],
        "payment_status": payment_status,
    }


class OrderProcessingTests(unittest.TestCase):
    def test_sample_orders_processed_once(self):
        product_catalog = copy.deepcopy(app.products)
        processed = app.process_all_orders(copy.deepcopy(app.orders), product_catalog)
        self.assertEqual([o["status"] for o in processed], ["paid", "paid", "pending"])
        self.assertEqual(product_catalog["P001"]["stock"], 9)
        self.assertEqual(product_catalog["P002"]["stock"], 48)
        self.assertEqual(product_catalog["P003"]["stock"], 18)
        self.assertEqual(product_catalog["P004"]["stock"], 14)

    def test_unknown_product_rejected(self):
        result = app.process_order(make_order(items=[{"product_id": "P999", "quantity": 1}]), fresh_products())
        self.assertEqual(result["status"], "rejected")

    def test_zero_negative_boolean_and_string_quantities_rejected(self):
        for quantity in (0, -1, True, "2"):
            with self.subTest(quantity=quantity):
                result = app.process_order(make_order(items=[{"product_id": "P001", "quantity": quantity}]), fresh_products())
                self.assertEqual(result["status"], "rejected")

    def test_insufficient_combined_stock_rejected_without_deduction(self):
        product_catalog = fresh_products()
        order = make_order(items=[{"product_id": "P001", "quantity": 1}, {"product_id": "P001", "quantity": 2}])
        result = app.process_order(order, product_catalog)
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(product_catalog["P001"]["stock"], 2)

    def test_missing_order_id_rejected(self):
        order = make_order()
        order.pop("order_id")
        self.assertEqual(app.process_order(order, fresh_products())["status"], "rejected")

    def test_blank_customer_rejected(self):
        self.assertEqual(app.process_order(make_order(customer="  "), fresh_products())["status"], "rejected")

    def test_non_dictionary_item_rejected(self):
        result = app.process_order(make_order(items=["not an item"]), fresh_products())
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(result["message"], "Invalid item format.")

    def test_empty_items_and_invalid_payment_rejected(self):
        self.assertEqual(app.process_order(make_order(items=[]), fresh_products())["status"], "rejected")
        self.assertEqual(app.process_order(make_order(payment_status="failed"), fresh_products())["status"], "rejected")

    def test_pending_order_has_quote_and_does_not_deduct_stock(self):
        product_catalog = fresh_products()
        result = app.process_order(make_order(payment_status="pending"), product_catalog)
        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["subtotal"], Decimal("25.00"))
        self.assertEqual(result["discount"], Decimal("0.00"))
        self.assertEqual(result["shipping"], Decimal("20.00"))
        self.assertEqual(result["total"], Decimal("45.00"))
        self.assertEqual(product_catalog["P002"]["stock"], 10)

    def test_unknown_option_rejected(self):
        result = app.process_order(make_order(), fresh_products(), apply_discout=False)
        self.assertEqual(result["status"], "rejected")
        self.assertIn("Unknown option", result["message"])

    def test_options_must_be_boolean(self):
        result = app.process_order(make_order(), fresh_products(), apply_discount="no")
        self.assertEqual(result["status"], "rejected")

    def test_discount_and_shipping_options(self):
        product_catalog = fresh_products()
        result = app.process_order(make_order(items=[{"product_id": "P001", "quantity": 1}]), product_catalog, apply_discount=False, include_shipping=False)
        self.assertEqual(result["discount"], Decimal("0.00"))
        self.assertEqual(result["shipping"], Decimal("0.00"))
        self.assertEqual(result["total"], Decimal("1200.00"))

    def test_duplicate_order_ids_normalised_in_batch(self):
        product_catalog = fresh_products()
        first = make_order(order_id=" ORD9 ", items=[{"product_id": "P001", "quantity": 1}])
        second = make_order(order_id="ord9", items=[{"product_id": "P001", "quantity": 1}])
        results = app.process_all_orders([first, second], product_catalog)
        self.assertEqual(results[0]["status"], "paid")
        self.assertEqual(results[0]["order_id"], "ORD9")
        self.assertEqual(results[1]["status"], "rejected")
        self.assertEqual(results[1]["message"], "Duplicate order ID.")
        self.assertEqual(product_catalog["P001"]["stock"], 1)

    def test_pending_order_id_is_reserved_after_acceptance(self):
        product_catalog = fresh_products()
        first = make_order(order_id=" pending-1 ", payment_status="pending")
        second = make_order(order_id="PENDING-1", payment_status="paid")
        results = app.process_all_orders([first, second], product_catalog)
        self.assertEqual(results[0]["status"], "pending")
        self.assertEqual(results[1]["status"], "rejected")
        self.assertEqual(product_catalog["P002"]["stock"], 10)

    def test_invalid_order_does_not_reserve_id(self):
        product_catalog = fresh_products()
        invalid = make_order(order_id=" X5 ", items=[])
        valid = make_order(order_id="x5", items=[{"product_id": "P002", "quantity": 1}])
        results = app.process_all_orders([invalid, valid], product_catalog)
        self.assertEqual(results[0]["status"], "rejected")
        self.assertEqual(results[1]["status"], "paid")

    def test_customer_names_are_normalised_in_reports(self):
        report = app.generate_customer_report([
            {"status": "paid", "customer": "Ali", "total": Decimal("1020.00")},
            {"status": "paid", "customer": "ali ", "total": Decimal("1020.00")},
            {"status": "paid", "customer": "Sara", "total": Decimal("1041.25")},
        ])
        self.assertEqual(report["customer_totals"]["Ali"], Decimal("2040.00"))
        self.assertEqual(report["top_customer"], "Ali")
        self.assertEqual(len(report["customer_totals"]), 2)

    def test_incomplete_product_data_does_not_crash_report(self):
        report = app.generate_product_report(
            [{"status": "paid", "items": [{"product_id": "P003", "quantity": 2}]}],
            {"P003": {"price": Decimal("1.00")}},
        )
        self.assertEqual(report["top_selling_product"], "P003")
        self.assertEqual(report["low_stock_products"], [])

    def test_decimal_half_up_rounding(self):
        self.assertEqual(app.money("2.675"), Decimal("2.68"))

    def test_batch_forwards_options(self):
        product_catalog = fresh_products()
        result = app.process_all_orders(
            [make_order(items=[{"product_id": "P001", "quantity": 1}])],
            product_catalog,
            apply_discount=False,
            include_shipping=False,
        )[0]
        self.assertEqual(result["discount"], Decimal("0.00"))
        self.assertEqual(result["shipping"], Decimal("0.00"))

    def test_sales_summary_can_be_tested_without_printing(self):
        summary = app.build_sales_summary([], {})
        self.assertEqual(summary["total_orders"], 0)
        self.assertEqual(summary["total_revenue"], Decimal("0.00"))
        self.assertEqual(summary["unique_paying_customers"], 0)

    def test_subtotal_function_and_sum_amounts_args(self):
        order = make_order(items=[{"product_id": "P001", "quantity": 1}, {"product_id": "P002", "quantity": 2}])
        self.assertEqual(app.calculate_order_subtotal(order, fresh_products()), Decimal("1250.00"))
        self.assertEqual(app.sum_amounts(1, "2.50", Decimal("0.25")), Decimal("3.75"))

    def test_subtotal_skips_unknown_product_instead_of_crashing(self):
        order = make_order(items=[{"product_id": "P999", "quantity": 1}])
        self.assertEqual(app.calculate_order_subtotal(order, fresh_products()), Decimal("0.00"))

    def test_low_stock_products_listed_and_threshold_configurable(self):
        catalog = fresh_products()
        catalog["P001"]["stock"] = 1
        report = app.generate_product_report([], catalog)
        self.assertEqual(report["low_stock_products"], ["Laptop"])
        report = app.generate_product_report([], catalog, low_stock_threshold=0)
        self.assertEqual(report["low_stock_products"], [])

    def test_ties_in_top_selling_products_listed_alphabetically(self):
        orders = [{"status": "paid", "items": [{"product_id": "P002", "quantity": 2}, {"product_id": "P001", "quantity": 2}]}]
        report = app.generate_product_report(orders, fresh_products())
        self.assertEqual(report["top_selling_product"], "Laptop, Mouse")

    def test_report_format_matches_assignment(self):
        import io
        from contextlib import redirect_stdout
        catalog = copy.deepcopy(app.products)
        processed = app.process_all_orders(copy.deepcopy(app.orders), catalog)
        summary = app.build_sales_summary(processed, catalog)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            app.print_sales_report(summary)
        text = buffer.getvalue()
        for expected in ("Total Orders: 3", "Paid Orders: 2", "Pending Orders: 1",
                         "Rejected Orders: 0", "Total Revenue: $1510.00",
                         "Total Discount: $210.00", "Total Shipping: $20.00",
                         "Top Customer: Ali", "Low Stock Products:\n- None"):
            self.assertIn(expected, text)

    def test_string_price_is_rejected(self):
        catalog = fresh_products()
        catalog["P002"]["price"] = "12.345"
        stock_before = catalog["P002"]["stock"]
        result = app.process_order(make_order(items=[{"product_id": "P002", "quantity": 1}]), catalog)
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(catalog["P002"]["stock"], stock_before)

    def test_pending_order_id_cannot_be_reused_as_paid_in_same_batch(self):
        pending = make_order(order_id="PEN1", payment_status="pending")
        paid = make_order(order_id="PEN1", payment_status="paid")
        results = app.process_all_orders([pending, paid], fresh_products())
        self.assertEqual([r["status"] for r in results], ["pending", "rejected"])

    def test_legb_demonstration(self):
        result = app.demonstrate_legb_scope()
        self.assertEqual(result["local"], "local scope")
        self.assertEqual(result["enclosing"], "enclosing scope")
        self.assertEqual(result["global"], "global scope")
        self.assertEqual(result["built_in_length"], len("enclosing scope"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
