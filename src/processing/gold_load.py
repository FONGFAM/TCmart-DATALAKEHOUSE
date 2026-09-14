"""
gold_load.py — PySpark Gold Zone Loader
Đọc dữ liệu đã được làm sạch từ Silver Zone (MinIO Parquet),
áp dụng surrogate key + SCD logic, ghi vào ClickHouse Gold (Star Schema).

Thứ tự load:
  1. Dimensions (Dim_Store, Dim_Product, Dim_Cashier, Dim_Customer, Dim_PaymentMethod)
  2. Facts (Fact_StoreSales, Fact_CashierShiftReconciliation)

Kỹ thuật:
  - Surrogate key: hash(natural_key) dùng xxhash64 → Int64
  - SCD Type 2 cho Dim_Store, Dim_Product: so sánh hash(attributes) để detect change
  - ReplacingMergeTree trên ClickHouse tự xử lý upsert qua version column (loaded_at)
"""
import sys
import os
import hashlib
from datetime import datetime, timedelta

# pyrefly: ignore [missing-import]
from pyspark.sql import SparkSession, DataFrame
# pyrefly: ignore [missing-import]
from pyspark.sql import functions as F
# pyrefly: ignore [missing-import
from pyspark.sql.types import LongType, StringType

# ─── Cấu hình ────────────────────────────────────────────────────────────────
SPARK_MASTER    = os.getenv("SPARK_MASTER", "local[2]")
MINIO_ENDPOINT  = os.getenv("MINIO_ENDPOINT", "http://tcmart-minio:9000")
MINIO_ACCESS    = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET    = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin2026")

CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "tcmart-clickhouse")
CLICKHOUSE_PORT = os.getenv("CLICKHOUSE_HTTP_PORT", "8123")
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "default")
CLICKHOUSE_PASS = os.getenv("CLICKHOUSE_PASSWORD", "tcmart2026")
CLICKHOUSE_DB   = "gold"

SILVER_BASE     = "s3a://silver-zone"
RAW_BASE        = "s3a://raw-zone/pos"

# ClickHouse JDBC URL (dùng clickhouse-jdbc driver)
CH_JDBC_URL = (
    f"jdbc:clickhouse://{CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}/{CLICKHOUSE_DB}"
    f"?user={CLICKHOUSE_USER}&password={CLICKHOUSE_PASS}"
)


# ─── Spark Session ────────────────────────────────────────────────────────────
def create_spark() -> SparkSession:
    return (SparkSession.builder
        .appName("tcmart_gold_load")
        .master(SPARK_MASTER)
        .config("spark.executor.memory", "512m")
        .config("spark.driver.memory", "512m")
        .config("spark.executor.cores", "1")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.jars",
                "/opt/spark/jars/clickhouse-jdbc-0.6.1-all.jar,"
                "/opt/spark/jars/mssql-jdbc-12.6.0.jre11.jar")
        .config("spark.hadoop.fs.s3a.endpoint",          MINIO_ENDPOINT)
        .config("spark.hadoop.fs.s3a.access.key",        MINIO_ACCESS)
        .config("spark.hadoop.fs.s3a.secret.key",        MINIO_SECRET)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .getOrCreate()
    )


# ─── Helpers ─────────────────────────────────────────────────────────────────
def natural_key_to_sk(col_name: str) -> F.Column:
    """Tạo surrogate key Int64 từ natural key String dùng xxhash64."""
    return F.xxhash64(F.col(col_name)).alias(col_name.replace("_id", "_sk"))


def write_to_clickhouse(df: DataFrame, table: str, mode: str = "append"):
    """Ghi DataFrame vào ClickHouse qua JDBC."""
    (df.write
       .format("jdbc")
       .option("url", CH_JDBC_URL)
       .option("dbtable", f"{CLICKHOUSE_DB}.{table}")
       .option("driver", "com.clickhouse.jdbc.ClickHouseDriver")
       .option("batchsize", "10000")
       .mode(mode)
       .save())
    print(f"  ✅ Written to {CLICKHOUSE_DB}.{table} ({mode})")


def truncate_table(table: str):
    """Xóa dữ liệu cũ trong bảng ClickHouse (dùng HTTP API)."""
    import requests
    url = f"http://{CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}/"
    sql = f"TRUNCATE TABLE IF EXISTS {CLICKHOUSE_DB}.{table}"
    resp = requests.post(url, data=sql, auth=(CLICKHOUSE_USER, CLICKHOUSE_PASS))
    if resp.status_code == 200:
        print(f"  🗑️  Truncated {CLICKHOUSE_DB}.{table}")
    else:
        print(f"  ⚠️  Truncate warning: {resp.text[:100]}")


# ─── Dimension Loaders ────────────────────────────────────────────────────────

def load_dim_payment_method(spark: SparkSession):
    """Static dimension — seed 5 phương thức thanh toán."""
    print("\n⏳ Loading Dim_PaymentMethod...")
    data = [
        (1, "CASH",        "Tiền mặt",              "TIỀN MẶT"),
        (2, "VIETQR",      "VietQR",                "CHUYỂN KHOẢN"),
        (3, "MOMO",        "Ví MoMo",               "VÍ ĐIỆN TỬ"),
        (4, "ZALOPAY",     "ZaloPay",               "VÍ ĐIỆN TỬ"),
        (5, "CREDIT_CARD", "Thẻ tín dụng / ghi nợ", "THẺ"),
    ]
    schema = ["payment_method_sk", "payment_method_code", "payment_method_name", "payment_group"]
    df = spark.createDataFrame(data, schema)
    truncate_table("Dim_PaymentMethod")
    write_to_clickhouse(df, "Dim_PaymentMethod")


def load_dim_store(spark: SparkSession, run_date: str):
    """
    Load Dim_Store từ raw stores Parquet.
    SCD Type 2: so sánh hash các thuộc tính thay đổi được.
    Đơn giản hóa: overwrite toàn bộ mỗi ngày (data nhỏ).
    """
    print("\n⏳ Loading Dim_Store...")
    try:
        stores = spark.read.parquet(f"{RAW_BASE}/stores/dt={run_date}/")
    except Exception as e:
        print(f"  ⚠️  No store data: {e}")
        return

    dim = (stores
        .withColumn("store_sk", F.xxhash64(F.col("store_id")))
        .withColumn("effective_start_date", F.lit(run_date).cast("date"))
        .withColumn("effective_end_date",   F.lit(None).cast("date"))
        .withColumn("is_current",           F.lit(1))
        .withColumn("dw_updated_at",        F.now())
        .select(
            "store_sk", "store_id", "store_name", "store_format",
            "region_id", "city", "floor_area_sqm", "is_active",
            "effective_start_date", "effective_end_date", "is_current",
            "dw_updated_at"
        )
    )

    truncate_table("Dim_Store")
    write_to_clickhouse(dim, "Dim_Store")
    print(f"  ✅ Dim_Store: {dim.count()} rows")


def load_dim_product(spark: SparkSession, run_date: str):
    """Load Dim_Product từ raw products Parquet + giá từ store_price_books."""
    print("\n⏳ Loading Dim_Product...")
    try:
        products = spark.read.parquet(f"{RAW_BASE}/products/dt={run_date}/")
    except Exception as e:
        print(f"  ⚠️  No product data: {e}")
        return

    # Giá bán lẻ: lấy từ price_books nếu có, fallback 0
    try:
        price_books = spark.read.parquet(f"{RAW_BASE}/store_price_books/dt={run_date}/")
        avg_price = (price_books
            .filter(F.col("effective_to").isNull())  # Đang hiệu lực
            .groupBy("product_id")
            .agg(F.avg("retail_price").alias("current_retail_price"))
        )
        products = products.join(avg_price, on="product_id", how="left")
    except Exception:
        products = products.withColumn("current_retail_price", F.lit(0.0))

    dim = (products
        .withColumn("product_sk",           F.xxhash64(F.col("product_id")))
        .withColumn("effective_start_date", F.lit(run_date).cast("date"))
        .withColumn("effective_end_date",   F.lit(None).cast("date"))
        .withColumn("is_current",           F.lit(1))
        .withColumn("dw_updated_at",        F.now())
        .withColumn("current_retail_price",
                    F.coalesce(F.col("current_retail_price"), F.lit(0.0)))
        .select(
            "product_sk", "product_id", "product_name", "department",
            "category_name", "base_uom", "is_weighted", "vat_rate",
            "current_retail_price",
            "effective_start_date", "effective_end_date", "is_current",
            "dw_updated_at"
        )
    )

    truncate_table("Dim_Product")
    write_to_clickhouse(dim, "Dim_Product")
    print(f"  ✅ Dim_Product: {dim.count()} rows")


def load_dim_cashier(spark: SparkSession, run_date: str):
    """Extract Dim_Cashier từ cashier_shifts (cashier_id + cashier_name)."""
    print("\n⏳ Loading Dim_Cashier...")
    try:
        shifts = spark.read.parquet(f"{RAW_BASE}/cashier_shifts/dt={run_date}/")
    except Exception as e:
        print(f"  ⚠️  No shift data: {e}")
        return

    dim = (shifts
        .select("cashier_id", "cashier_name")
        .distinct()
        .withColumn("cashier_sk", F.xxhash64(F.col("cashier_id")))
        .withColumn("status", F.lit("ACTIVE"))
        .select("cashier_sk", "cashier_id", "cashier_name", "status")
    )

    truncate_table("Dim_Cashier")
    write_to_clickhouse(dim, "Dim_Cashier")
    print(f"  ✅ Dim_Cashier: {dim.count()} rows")


def load_dim_customer(spark: SparkSession, run_date: str):
    """Load Dim_Customer từ raw customers Parquet."""
    print("\n⏳ Loading Dim_Customer...")
    try:
        customers = spark.read.parquet(f"{RAW_BASE}/customers/dt={run_date}/")
    except Exception as e:
        print(f"  ⚠️  No customer data: {e}")
        return

    dim = (customers
        .withColumn("customer_sk",
                    F.xxhash64(F.col("customer_id").cast("string")))
        .withColumn("customer_id_str", F.col("customer_id").cast("string"))
        .select(
            "customer_sk",
            F.col("customer_id_str").alias("customer_id"),
            "loyalty_tier",
            F.col("registered_store_id")
        )
    )

    truncate_table("Dim_Customer")
    write_to_clickhouse(dim, "Dim_Customer")
    print(f"  ✅ Dim_Customer: {dim.count()} rows")


# ─── Fact Loaders ─────────────────────────────────────────────────────────────

def load_fact_store_sales(spark: SparkSession, run_date: str):
    """
    Load Fact_StoreSales từ Silver sales_line_items.
    Join với Dim tables để lấy Surrogate Keys.
    """
    print("\n⏳ Loading Fact_StoreSales...")
    try:
        line_items = spark.read.parquet(f"{SILVER_BASE}/sales_line_items/")
        # Chỉ lấy của run_date
        line_items = line_items.filter(
            F.col("invoice_date_dt") == F.lit(run_date).cast("date")
        )
    except Exception as e:
        print(f"  ⚠️  No silver line items: {e}")
        return

    count = line_items.count()
    if count == 0:
        print(f"  ⚠️  No line items for {run_date}")
        return

    # Lookup bảng SK (từ ClickHouse hiện tại — dùng HTTP để lấy mapping nhỏ)
    import requests

    def fetch_sk_map(table: str, id_col: str, sk_col: str) -> dict:
        """Lấy mapping {natural_key: sk} từ ClickHouse."""
        url = f"http://{CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}/"
        sql = f"SELECT {id_col}, {sk_col} FROM {CLICKHOUSE_DB}.{table} FORMAT JSONCompact"
        r = requests.post(url, data=sql, auth=(CLICKHOUSE_USER, CLICKHOUSE_PASS), timeout=30)
        result = {}
        if r.status_code == 200:
            data = r.json()
            for row in data.get("data", []):
                result[str(row[0])] = int(row[1])
        return result

    store_sk_map   = fetch_sk_map("Dim_Store",         "store_id",          "store_sk")
    product_sk_map = fetch_sk_map("Dim_Product",       "product_id",        "product_sk")
    pm_sk_map      = fetch_sk_map("Dim_PaymentMethod", "payment_method_code", "payment_method_sk")

    # UDFs để map sang SK
    @F.udf(LongType())
    def get_store_sk(sid):
        return store_sk_map.get(str(sid), -1)

    @F.udf(LongType())
    def get_product_sk(pid):
        return product_sk_map.get(str(pid), -1)

    @F.udf(LongType())
    def get_pm_sk(method):
        return pm_sk_map.get(str(method or "CASH"), 1)

    # Tạo date_sk từ invoice_date
    fact = (line_items
        .withColumn("invoice_item_sk",
                    F.xxhash64(F.col("invoice_item_id").cast("string")))
        .withColumn("date_sk",
                    F.date_format(F.col("invoice_date_dt"), "yyyyMMdd").cast("int"))
        .withColumn("store_sk",          get_store_sk(F.col("store_id")))
        .withColumn("product_sk",        get_product_sk(F.col("product_id")))
        .withColumn("payment_method_sk", get_pm_sk(F.lit("CASH")))  # Default; join với tenders ở phase 4 nâng cao
        .withColumn("customer_sk",
                    F.when(F.col("customer_id").isNotNull(),
                           F.xxhash64(F.col("customer_id").cast("string")))
                    .otherwise(F.lit(None).cast("long")))
        .withColumn("net_sales_vnd",
                    F.when(F.col("is_return") == 1, -F.col("line_total_amount"))
                    .otherwise(F.col("line_total_amount")))
        .withColumn("dq_run_date",  F.lit(run_date).cast("date"))
        .withColumn("loaded_at",    F.now())
        .select(
            "invoice_item_sk",
            F.col("invoice_id"),
            "date_sk", "store_sk", "product_sk", "customer_sk", "payment_method_sk",
            F.col("shift_id"),
            "quantity",
            F.col("unit_price").alias("unit_price_vnd"),
            F.col("line_discount_amount").alias("discount_amount_vnd"),
            "net_sales_vnd",
            F.col("is_return"),
            "dq_run_date", "loaded_at"
        )
    )

    # Chỉ insert các row có store và product hợp lệ
    valid_fact = fact.filter((F.col("store_sk") != -1) & (F.col("product_sk") != -1))
    invalid_count = fact.count() - valid_fact.count()

    if invalid_count > 0:
        print(f"  ⚠️  Dropped {invalid_count} rows with invalid store/product SK")

    write_to_clickhouse(valid_fact, "Fact_StoreSales")
    print(f"  ✅ Fact_StoreSales: {valid_fact.count()} rows for {run_date}")


def load_fact_shift_reconciliation(spark: SparkSession, run_date: str):
    """
    Load Fact_CashierShiftReconciliation từ Silver cashier_shift_reconciliation Parquet.
    """
    print("\n⏳ Loading Fact_CashierShiftReconciliation...")
    try:
        reconciled = spark.read.parquet(
            f"{SILVER_BASE}/cashier_shift_reconciliation/dt={run_date}/"
        )
    except Exception as e:
        print(f"  ⚠️  No reconciliation data: {e}")
        return

    import requests

    def fetch_sk_map(table: str, id_col: str, sk_col: str) -> dict:
        url = f"http://{CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}/"
        sql = f"SELECT {id_col}, {sk_col} FROM {CLICKHOUSE_DB}.{table} FORMAT JSONCompact"
        r = requests.post(url, data=sql, auth=(CLICKHOUSE_USER, CLICKHOUSE_PASS), timeout=30)
        result = {}
        if r.status_code == 200:
            for row in r.json().get("data", []):
                result[str(row[0])] = int(row[1])
        return result

    store_sk_map   = fetch_sk_map("Dim_Store",   "store_id",   "store_sk")
    cashier_sk_map = fetch_sk_map("Dim_Cashier", "cashier_id", "cashier_sk")

    @F.udf(LongType())
    def get_store_sk(sid):
        return store_sk_map.get(str(sid), -1)

    @F.udf(LongType())
    def get_cashier_sk(cid):
        return cashier_sk_map.get(str(cid), -1)

    fact = (reconciled
        .withColumn("shift_sk",   F.xxhash64(F.col("shift_id")))
        .withColumn("date_sk",
                    F.date_format(F.to_date(F.col("closed_at")), "yyyyMMdd").cast("int"))
        .withColumn("store_sk",   get_store_sk(F.col("store_id")))
        .withColumn("cashier_sk", get_cashier_sk(F.col("cashier_id")))
        .withColumn("dq_run_date", F.lit(run_date).cast("date"))
        .withColumn("loaded_at",   F.now())
        .select(
            "shift_sk", "shift_id",
            "store_sk", "date_sk", "cashier_sk",
            "terminal_id",
            "opening_cash_float",
            F.col("total_cash_sales_vnd").alias("system_total_cash_sales"),
            "actual_closing_cash",
            F.col("computed_cash_variance").alias("cash_variance"),
            "anomaly_flag",
            F.col("total_qr_sales_vnd").alias("system_total_qr_sales"),
            F.col("total_ewallet_sales_vnd").alias("system_total_ewallet_sales"),
            "total_fx_sales_cashier_rate",
            "total_fx_sales_reference",
            "fx_rate_variance_vnd",
            "dq_run_date", "loaded_at"
        )
        .filter(F.col("store_sk") != -1)
    )

    write_to_clickhouse(fact, "Fact_CashierShiftReconciliation")
    print(f"  ✅ Fact_CashierShiftReconciliation: {fact.count()} rows for {run_date}")


# ─── MAIN ────────────────────────────────────────────────────────────────────
def main(run_date: str = None):
    if run_date is None:
        from datetime import date
        run_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    print("=" * 60)
    print(f"  TC Mart Gold Load | run_date={run_date}")
    print("=" * 60)

    spark = create_spark()
    spark.sparkContext.setLogLevel("WARN")

    try:
        # 1. Dimensions (thứ tự quan trọng — Facts phụ thuộc SKs)
        load_dim_payment_method(spark)
        load_dim_store(spark, run_date)
        load_dim_product(spark, run_date)
        load_dim_cashier(spark, run_date)
        load_dim_customer(spark, run_date)

        # 2. Facts
        load_fact_store_sales(spark, run_date)
        load_fact_shift_reconciliation(spark, run_date)

        print("\n" + "=" * 60)
        print("  ✅ Gold Load COMPLETE!")
        print("=" * 60)

    finally:
        spark.stop()


if __name__ == "__main__":
    run_dt = sys.argv[1] if len(sys.argv) > 1 else None
    main(run_dt)
