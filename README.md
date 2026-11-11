# E-Commerce Order Processing System

A command-line Python assessment project using only the Python standard library. It uses functions and in-memory dictionaries/lists; it does not require a database, framework, API, or external package.

## Files
- `ecommerce_order_processing.py` — business logic, sample data, reports, and CLI entry point.
- `test_ecommerce.py` — automated tests using `unittest`.
- `.gitignore` — excludes Python cache files.

## Requirements
Python 3.10 or newer. No third-party packages are needed.

## Run the program
```bash
python ecommerce_order_processing.py
```

## Run the tests
```bash
python -m unittest -v
```

## Business rules and assumptions
- Products have an ID, name, price, category, and available stock.
- Orders require a non-empty ID and customer name, a non-empty list of items, and payment status `paid` or `pending`.
- Order IDs are trimmed and uppercased. Duplicate IDs within a batch are rejected.
- Customer names are trimmed and grouped case-insensitively in reports.
- Each item must reference an existing product and have a positive integer quantity; booleans are not accepted as quantities.
- Requested quantities for repeated product lines are checked together against stock.
- Pending orders show a subtotal, discount, shipping, and total quote, but do not deduct inventory and do not contribute to paid revenue.
- Only paid orders deduct stock and contribute to sales/customer/product reports.
- Discount tiers: 15% for subtotals of at least 1000; 10% for at least 500; 5% for at least 200; otherwise no discount.
- Shipping is free for subtotals of at least 500; otherwise it costs 20.
- Monetary calculations use `Decimal` and `ROUND_HALF_UP` to round to two decimal places.
- Revenue is the amount customers pay: subtotal minus discount plus shipping, for paid orders only.
- The low-stock threshold is fewer than 5 units (the assignment does not give one). It is the default of the `low_stock_threshold` parameter and can be changed with `LOW_STOCK_THRESHOLD` or by passing another value.
- The printed report follows the assignment's expected format exactly.
- Top customer is ranked by total spending; ties are listed alphabetically.
- `apply_discount` and `include_shipping` are the only accepted processing options, and both must be booleans.
- `sum_amounts(*amounts)` adds any number of money values and is used for the report totals (`*args`).
- `process_order()` accepts additional item dictionaries through `*items_to_process` to demonstrate `*args`, and keyword options through `**options`.
- Inventory is in memory and resets when the program restarts.

## Python features demonstrated
Functions, return values, positional and keyword arguments, `*args`, `**kwargs`, dictionaries, lists, sets, comprehensions, sorting with a key function, LEGB scope, input validation, `Decimal`, and automated tests with `unittest`.
- A pending order's ID is recorded, so the same ID cannot be sent again as `paid` in the same batch (it is rejected as a duplicate).
- Product prices must be numbers (`int`, `float` or `Decimal`); string prices are rejected.
