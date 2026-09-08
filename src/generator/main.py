"""
main.py — Entry point cho Data Generator TCmart
Usage:
  python main.py --db all              # Sinh toàn bộ 12 DBs
  python main.py --db product_db       # Chỉ sinh 1 DB
  python main.py --db ecommerce_db retail_pos_db   # Nhiều DB
"""
import argparse
import sys
from tqdm import tqdm

# ─── Danh sách generator (thứ tự quan trọng — FK dependencies) ───────────────
GENERATORS = {
    # 1. Master data trước
    "exchange_rate_db": "generators.gen_exchange_rate",
    "product_db":       "generators.gen_product",
    "employee_db":      "generators.gen_employee",

    # 2. Source DBs phụ thuộc master data
    "procurement_db":   "generators.gen_procurement",
    "warehouse_db":     "generators.gen_warehouse",
    "production_db":    "generators.gen_production",

    # 3. Sales channels
    "retail_pos_db":    "generators.gen_retail_pos",
    "ecommerce_db":     "generators.gen_ecommerce",
    "franchise_db":     "generators.gen_franchise",

    # 4. Supporting domains
    "promotion_db":     "generators.gen_promotion",
    "marketing_db":     "generators.gen_marketing",
    "invoice_db":       "generators.gen_invoice",
}

ALL_DBS = list(GENERATORS.keys())


def run_generator(db_name: str) -> None:
    """Chạy generator cho một database cụ thể."""
    import importlib
    module_path = GENERATORS[db_name]
    try:
        module = importlib.import_module(module_path)
        print(f"\n{'─'*50}")
        print(f"  Generating: {db_name}")
        print(f"{'─'*50}")
        module.run()
        print(f"  ✅ {db_name} — DONE")
    except Exception as e:
        print(f"  ❌ {db_name} — FAILED: {e}", file=sys.stderr)
        raise


def main():
    parser = argparse.ArgumentParser(
        description="TCmart Data Generator — sinh dữ liệu mẫu cho Source DBs"
    )
    parser.add_argument(
        "--db",
        nargs="+",
        choices=ALL_DBS + ["all"],
        default=["all"],
        help="Tên database cần sinh dữ liệu. Dùng 'all' để sinh toàn bộ.",
    )
    args = parser.parse_args()

    target_dbs = ALL_DBS if "all" in args.db else args.db

    print(f"\n{'═'*50}")
    print(f"  TCmart Data Generator v1.0")
    print(f"  Target: {', '.join(target_dbs)}")
    print(f"{'═'*50}")

    for db_name in tqdm(target_dbs, desc="Overall Progress"):
        run_generator(db_name)

    print(f"\n{'═'*50}")
    print(f"  🎉 Hoàn tất sinh dữ liệu!")
    print(f"  Chạy 'make gen-dirty' để nhồi ~5% dữ liệu lỗi.")
    print(f"{'═'*50}\n")


if __name__ == "__main__":
    main()
