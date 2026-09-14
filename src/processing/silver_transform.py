"""
silver_transform.py — PySpark Silver Zone Transformation
Đọc raw Parquet từ MinIO, áp dụng Business Logic và Data Quality, ghi Silver Zone.

Business Logic:
  1. Quy đổi ngoại tệ về VND chuẩn
  2. Tính cash_variance per shift
  3. Gắn cờ is_return từ sales_returns
  4. Detect anomaly FX rate so với Dim_ExchangeRate tham chiếu
  5. Viết bản ghi vi phạm vào Quarantine Zone
"""
import sys
import os
from datetime import datetime, timedelta

# pyrefly: ignore [missing-import]
from pyspark.sql import SparkSession
# pyrefly: ignore [missing-import]
from pyspark.sql import functions as F
# pyrefly: ignore [missing-import]
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType,
    LongType, TimestampType, IntegerType, DateType
)

# ─── Cấu hình ────────────────────────────────────────────────────────────────
SPARK_MASTER   = os.getenv("SPARK_MASTER", "local[2]")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://tcmart-minio:9000")
MINIO_ACCESS   = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET   = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin2026")

CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "tcmart-clickhouse")
CLICKHOUSE_PORT = os.getenv("CLICKHOUSE_HTTP_PORT", "8123")
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "default")
CLICKHOUSE_PASS = os.getenv("CLICKHOUSE_PASSWORD", "tcmart2026")

RAW_BASE        = "s3a://raw-zone/pos"
SILVER_BASE     = "s3a://silver-zone"
QUARANTINE_BASE = "s3a://quarantine-zone"

# Ngưỡng phát hiện bất thường
CASH_VARIANCE_THRESHOLD   = 50_000.0    # VND — chênh lệch tiền mặt cảnh báo
FX_RATE_DEVIATION_PCT     = 0.05        # 5% deviation vs rate tham chiếu
FX_RATE_INVALID_THRESHOLD = 100.0       # exchange_rate < 100 VND/USD là bất thường


def create_spark() -> SparkSession:
    return (SparkSession.builder
        .appName("tcmart_silver_transform")
        .master(SPARK_MASTER)
        .config("spark.executor.memory", "512m")
        .config("spark.driver.memory", "512m")
        .config("spark.executor.cores", "1")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.jars", "/opt/spark/jars/mssql-jdbc-12.6.0.jre11.jar,"
                              "/opt/spark/jars/clickhouse-jdbc-0.6.1-all.jar")
        .config("spark.hadoop.fs.s3a.endpoint",           MINIO_ENDPOINT)
        .config("spark.hadoop.fs.s3a.access.key",         MINIO_ACCESS)
        .config("spark.hadoop.fs.s3a.secret.key",         MINIO_SECRET)
        .config("spark.hadoop.fs.s3a.path.style.access",  "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .getOrCreate()
    )


# ─── Tiện ích ─────────────────────────────────────────────────────────────────

def standardize_dataframe(df, unique_cols: list = None):
    """
    Chuẩn hóa Dataframe cơ bản:
    - Trim khoảng trắng các cột String.
    - Xóa trùng lặp theo unique_cols.
    """
    for field in df.schema.fields:
        if isinstance(field.dataType, StringType):
            df = df.withColumn(field.name, F.trim(F.col(field.name)))
            
    if unique_cols:
        before = df.count()
        df = df.dropDuplicates(unique_cols)
        after = df.count()
        if before > after:
            print(f"  ℹ️  Deduplicated {before - after} records based on {unique_cols}")
            
    return df


# ─── DQ: Kiểm tra Exchange Rate ──────────────────────────────────────────────
def validate_and_fix_exchange_rates(spark: SparkSession, run_date: str):
    """
    [DQ Gate] Kiểm tra exchange_rate trong sales_payment_tenders:
    - Hợp lệ  → ghi vào silver-zone
    - Vi phạm → ghi vào quarantine-zone + in ra log
    """
    print("\n⏳ [DQ] Validating exchange rates...")

    # Đọc raw tenders
    tenders_path = f"{RAW_BASE}/sales_payment_tenders/dt={run_date}/"
    try:
        tenders = spark.read.parquet(tenders_path)
        tenders = standardize_dataframe(tenders, ["tender_id", "invoice_id"])
    except Exception as e:
        print(f"  ⚠️  No tender data for {run_date}: {e}")
        return

    # Lấy tỷ giá tham chiếu từ ClickHouse Dim_ExchangeRate
    # Đọc qua HTTP (không cần Spark JDBC cho bảng nhỏ)
    import requests
    ref_url = (f"http://{CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}/"
               f"?query=SELECT currency_code, reference_rate_vnd "
               f"FROM gold.Dim_ExchangeRate WHERE rate_date='{run_date}' "
               f"FORMAT JSON")
    ref_rates = {}
    try:
        resp = requests.get(ref_url, auth=(CLICKHOUSE_USER, CLICKHOUSE_PASS), timeout=10)
        for row in resp.json().get("data", []):
            ref_rates[row["currency_code"]] = float(row["reference_rate_vnd"])
    except Exception as e:
        print(f"  ⚠️  Could not fetch reference rates: {e}")
        # Fallback tỷ giá tĩnh
        ref_rates = {"USD": 25400.0, "CNY": 3500.0, "EUR": 27800.0}

    # Broadcast reference rates
    ref_broadcast = spark.sparkContext.broadcast(ref_rates)

    # UDF kiểm tra tỷ giá
    @F.udf(StringType())
    def check_rate_udf(currency, rate):
        if currency == "VND":
            return "VALID"
        ref = ref_broadcast.value.get(currency)
        if rate is None or rate <= 0:
            return "INVALID_ZERO_OR_NEGATIVE"
        if rate == 1.0 and currency != "VND":
            return "INVALID_FORGOT_TO_CONVERT"
        if ref is None:
            return "UNKNOWN_CURRENCY"
        deviation = abs(rate - ref) / ref
        if deviation > FX_RATE_DEVIATION_PCT * 5:  # >25% deviation → definitely wrong
            return "INVALID_EXTREME_DEVIATION"
        if deviation > FX_RATE_DEVIATION_PCT:
            return "WARNING_HIGH_DEVIATION"
        return "VALID"

    tenders_checked = tenders.withColumn(
        "dq_rate_status",
        check_rate_udf(F.col("currency_code"), F.col("exchange_rate"))
    ).withColumn(
        "dq_checked_at", F.lit(run_date)
    ).withColumn(
        "dq_pipeline", F.lit("silver_transform")
    )

    # Tách: hợp lệ vs vi phạm
    valid    = tenders_checked.filter(F.col("dq_rate_status").isin(["VALID", "WARNING_HIGH_DEVIATION"]))
    invalid  = tenders_checked.filter(~F.col("dq_rate_status").isin(["VALID", "WARNING_HIGH_DEVIATION"]))

    n_valid   = valid.count()
    n_invalid = invalid.count()

    print(f"  ✅ Valid tenders:    {n_valid}")
    print(f"  ❌ Invalid tenders:  {n_invalid}")

    if n_invalid > 0:
        # Ghi vào MinIO Staging Zone để Data Steward App (FastAPI) đọc
        staging_path = f"s3a://staging-zone/suspect_data/sales_payment_tenders/dt={run_date}/"
        invalid.write.mode("append").parquet(staging_path)
        print(f"  ⚠️  Pushed {n_invalid} suspect records to {staging_path} for manual review.")

    # Ghi Silver
    valid.write.mode("overwrite").parquet(
        f"{SILVER_BASE}/sales_payment_tenders/dt={run_date}/"
    )
    return valid, ref_rates


# ─── Transform: Tính Shift Reconciliation ────────────────────────────────────
def build_shift_reconciliation(spark: SparkSession, run_date: str, valid_tenders, ref_rates: dict):
    """
    Aggregate tenders theo shift_id để tạo bảng đối soát ca.
    Join với cashier_shifts để tính cash_variance và fx_rate_variance.
    """
    print("\n⏳ Building shift reconciliation...")

    shifts_path = f"{RAW_BASE}/cashier_shifts/dt={run_date}/"
    invoices_path = f"{RAW_BASE}/sales_invoices/dt={run_date}/"

    try:
        shifts   = spark.read.parquet(shifts_path)
        invoices = spark.read.parquet(invoices_path)
        
        shifts = standardize_dataframe(shifts, ["shift_id"])
        invoices = standardize_dataframe(invoices, ["invoice_id"])
    except Exception as e:
        print(f"  ⚠️  Missing data for reconciliation: {e}")
        return

    # Join invoices với tenders để biết shift nào có bao nhiêu cash/QR
    inv_with_shift = invoices.select("invoice_id", "shift_id")
    tenders_with_shift = valid_tenders.join(inv_with_shift, on="invoice_id", how="left")

    # Aggregate per shift
    shift_agg = (tenders_with_shift
        .groupBy("shift_id")
        .agg(
            F.sum(F.when(F.col("payment_method") == "CASH", F.col("tender_amount_vnd")).otherwise(0))
             .alias("total_cash_sales_vnd"),
            F.sum(F.when(F.col("payment_method") == "VIETQR", F.col("tender_amount_vnd")).otherwise(0))
             .alias("total_qr_sales_vnd"),
            F.sum(F.when(F.col("payment_method").isin(["MOMO", "ZALOPAY"]), F.col("tender_amount_vnd")).otherwise(0))
             .alias("total_ewallet_sales_vnd"),
            # FX: Tính lại theo tỷ giá tham chiếu
            F.sum(F.when(F.col("currency_code") != "VND", F.col("tender_amount_original")).otherwise(0))
             .alias("total_fx_amount_original"),
            F.sum(F.when(F.col("currency_code") != "VND", F.col("tender_amount_vnd")).otherwise(0))
             .alias("total_fx_sales_cashier_rate"),
        )
    )

    # Tính fx_sales theo tỷ giá tham chiếu
    # (Simplified: dùng avg ref rate, production cần join per-currency)
    avg_ref = sum(ref_rates.values()) / max(len(ref_rates), 1) if ref_rates else 25400.0

    shift_reconciled = (shifts
        .join(shift_agg, on="shift_id", how="left")
        .withColumn("total_cash_sales_vnd",       F.coalesce(F.col("total_cash_sales_vnd"), F.lit(0.0)))
        .withColumn("total_qr_sales_vnd",          F.coalesce(F.col("total_qr_sales_vnd"), F.lit(0.0)))
        .withColumn("total_ewallet_sales_vnd",     F.coalesce(F.col("total_ewallet_sales_vnd"), F.lit(0.0)))
        .withColumn("total_fx_sales_cashier_rate", F.coalesce(F.col("total_fx_sales_cashier_rate"), F.lit(0.0)))
        .withColumn("total_fx_amount_original",    F.coalesce(F.col("total_fx_amount_original"), F.lit(0.0)))
        # Tính lại doanh thu FX theo tỷ giá tham chiếu (avg)
        .withColumn("total_fx_sales_reference",
                    F.col("total_fx_amount_original") * F.lit(avg_ref))
        .withColumn("fx_rate_variance_vnd",
                    F.col("total_fx_sales_reference") - F.col("total_fx_sales_cashier_rate"))
        # cash_variance = actual_closing_cash - (opening_float + total_cash_sales)
        .withColumn("computed_cash_variance",
                    F.col("actual_closing_cash") - (F.col("opening_cash_float") + F.col("total_cash_sales_vnd")))
        .withColumn("anomaly_flag",
                    F.when(F.abs(F.col("computed_cash_variance")) > CASH_VARIANCE_THRESHOLD,
                           F.when(F.col("computed_cash_variance") < 0, F.lit("ANOMALY_DEFICIT"))
                            .otherwise(F.lit("ANOMALY_SURPLUS")))
                    .otherwise(F.lit("NORMAL")))
        .withColumn("dq_run_date", F.lit(run_date))
    )

    n_anomaly = shift_reconciled.filter(F.col("anomaly_flag") != "NORMAL").count()
    print(f"  ✅ Shift reconciliation built: {shift_reconciled.count()} shifts")
    print(f"  ⚠️  Anomaly shifts: {n_anomaly}")

    # Ghi Silver
    shift_reconciled.write.mode("overwrite").parquet(
        f"{SILVER_BASE}/cashier_shift_reconciliation/dt={run_date}/"
    )


# ─── Transform: Sales Line Items (Fact_StoreSales source) ────────────────────
def build_sales_line_items(spark: SparkSession, run_date: str):
    """
    Join invoices + items + returns để tạo bảng denormalized cấp dòng sản phẩm.
    Gắn cờ is_return cho dòng đổi/trả.
    """
    print("\n⏳ Building sales line items (Silver)...")

    try:
        items    = spark.read.parquet(f"{RAW_BASE}/sales_invoice_items/dt={run_date}/")
        invoices = spark.read.parquet(f"{RAW_BASE}/sales_invoices/dt={run_date}/")
        returns  = spark.read.parquet(f"{RAW_BASE}/sales_returns/dt={run_date}/")
        products = spark.read.parquet(f"{RAW_BASE}/products/dt={run_date}/")
        stores   = spark.read.parquet(f"{RAW_BASE}/stores/dt={run_date}/")
        
        items = standardize_dataframe(items, ["invoice_item_id"])
        invoices = standardize_dataframe(invoices, ["invoice_id"])
    except Exception as e:
        print(f"  ⚠️  Missing data for line items: {e}")
        return

    # Bộ invoice_ids bị đổi/trả
    returned_invoices = returns.select("original_invoice_id").distinct()

    # Join tất cả
    line_items = (items
        .join(invoices.select("invoice_id", "store_id", "cashier_id",
                               "customer_id", "invoice_date", "shift_id"),
              on="invoice_id", how="inner")
        .join(products.select("product_id", "department", "category_name", "base_uom"),
              on="product_id", how="left")
        .join(stores.select("store_id", "store_format", "region_id"),
              on="store_id", how="left")
        # Gắn cờ is_return
        .withColumn("is_return",
                    F.col("invoice_id").isin(
                        [r["original_invoice_id"] for r in returned_invoices.collect()]
                    ).cast("int"))
        .withColumn("net_sales_vnd",
                    F.when(F.col("is_return") == 1,
                           -F.col("line_total_amount"))
                    .otherwise(F.col("line_total_amount")))
        .withColumn("invoice_date_dt",
                    F.to_date(F.col("invoice_date")))
        .withColumn("dq_run_date", F.lit(run_date))
    )

    count = line_items.count()
    print(f"  ✅ Sales line items Silver: {count} rows")

    line_items.write.mode("overwrite").partitionBy("invoice_date_dt").parquet(
        f"{SILVER_BASE}/sales_line_items/"
    )


# ─── MAIN ────────────────────────────────────────────────────────────────────
def main(run_date: str = None):
    if run_date is None:
        run_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    print("=" * 60)
    print(f"  TC Mart Silver Transformation | run_date={run_date}")
    print("=" * 60)

    spark = create_spark()
    spark.sparkContext.setLogLevel("WARN")

    try:
        # 1. DQ + fix exchange rates
        result = validate_and_fix_exchange_rates(spark, run_date)
        if result is None:
            print("  ⚠️  No tender data, skipping downstream transforms")
            return
        valid_tenders, ref_rates = result

        # 2. Shift reconciliation
        build_shift_reconciliation(spark, run_date, valid_tenders, ref_rates)

        # 3. Sales line items
        build_sales_line_items(spark, run_date)

        print("\n" + "=" * 60)
        print("  ✅ Silver transformation COMPLETE!")
        print("=" * 60)

    finally:
        spark.stop()


if __name__ == "__main__":
    run_dt = sys.argv[1] if len(sys.argv) > 1 else None
    main(run_dt)
