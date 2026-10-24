"""Generate a reproducible sales.csv for the HDFS classroom lab (Python 3)."""
import argparse
import csv
from pathlib import Path

PRODUCTS = [("Laptop", 800), ("Mouse", 20), ("Keyboard", 50), ("Monitor", 250)]


def main():
    parser = argparse.ArgumentParser(description="Create a realistic multi-block sales CSV")
    parser.add_argument("--rows", type=int, default=500_000, help="Number of sales rows (default: 500000)")
    parser.add_argument("--output", type=Path, default=Path("data/sales.csv"), help="Output CSV path")
    args = parser.parse_args()
    if args.rows < 1:
        parser.error("--rows must be positive")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["OrderID", "Product", "Quantity", "Price"])
        for i in range(1, args.rows + 1):
            product, price = PRODUCTS[(i - 1) % len(PRODUCTS)]
            writer.writerow([i, product, 1 + (i % 5), price])
    size_mib = args.output.stat().st_size / (1024 * 1024)
    print(f"Created {args.output} with {args.rows:,} sales records ({size_mib:.2f} MiB)")


if __name__ == "__main__":
    main()
