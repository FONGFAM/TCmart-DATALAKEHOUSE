"""
dag_02_ingestion.py — Airflow DAG
Trích xuất dữ liệu từ SQL Server (retail_pos_db) vào MinIO (Raw Zone) mỗi giờ.
Dùng PySpark JDBC để đọc batch incremental.

Lịch chạy:
  - Mỗi giờ: sales_invoices, sales_invoice_items, sales_payment_tenders
  - Cuối ngày (23h): cashier_shifts (đóng ca), sales_returns, store_inventory_snapshots
  - 1 lần/ngày (00h): products, product_barcodes, store_price_books, stores, customers
"""
# pyrefly: ignore [missing-import]
from airflow import DAG
# pyrefly: ignore [missing-import]
from airflow.operators.python import PythonOperator
# pyrefly: ignore [missing-import]
from airflow.operators.empty import EmptyOperator
from datetime import datetime, timedelta
import os
import subprocess

# ─── Cấu hình kết nối ────────────────────────────────────────────────────────
MSSQL_HOST  = os.getenv("MSSQL_HOST", "tcmart-mssql")
MSSQL_PORT  = os.getenv("MSSQL_PORT", "1433")
MSSQL_DB    = "retail_pos_db"
MSSQL_USER  = os.getenv("SA_USER", "sa")
MSSQL_PASS  = os.getenv("SA_PASSWORD", "TCMart@2026!Strong")

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://tcmart-minio:9000")
MINIO_ACCESS   = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET   = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin2026")

SPARK_MASTER   = os.getenv("SPARK_MASTER", "local[2]")

JDBC_URL = (
    f"jdbc:sqlserver://{MSSQL_HOST}:{MSSQL_PORT};"
    f"databaseName={MSSQL_DB};encrypt=true;trustServerCertificate=true;"
    f"user={MSSQL_USER};password={MSSQL_PASS}"
)

# ─── Helper: Chạy PySpark Job ─────────────────────────────────────────────────
def run_spark_ingest(table_name: str, mode: str = "incremental",
                     ts_column: str = None, custom_where: str = None, lookback_hours: int = 2, **context):
    """
    Chạy PySpark job đọc SQL Server qua JDBC và lưu Parquet vào MinIO.
    mode = 'incremental' (dùng ts_column hoặc custom_where) | 'full' (toàn bộ bảng)
    """
    # pyrefly: ignore [missing-import]
    from pyspark.sql import SparkSession
    from datetime import datetime, timezone

    run_ts   = context["ts"]   # Execution timestamp của Airflow
    run_date = context["ds"]   # YYYY-MM-DD

    print(f"⏳ Ingesting [{table_name}] mode={mode} run_ts={run_ts}")

    spark = (SparkSession.builder
        .appName(f"tcmart_ingest_{table_name}")
        .master(SPARK_MASTER)
        .config("spark.executor.memory", "512m")
        .config("spark.driver.memory", "512m")
        .config("spark.executor.cores", "1")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.jars", "/opt/spark/jars/mssql-jdbc-12.6.0.jre11.jar")
        .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT)
        .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS)
        .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    try:
        if mode == "incremental":
            cutoff = (datetime.fromisoformat(run_ts.replace("Z", ""))
                      - timedelta(hours=lookback_hours))
            cutoff_str = cutoff.strftime('%Y-%m-%d %H:%M:%S')
            
            if custom_where:
                where_clause = custom_where.format(cutoff=cutoff_str)
                query = f"(SELECT * FROM dbo.{table_name} WHERE {where_clause}) t"
            elif ts_column:
                query = f"(SELECT * FROM dbo.{table_name} WHERE {ts_column} >= '{cutoff_str}') t"
            else:
                query = f"(SELECT * FROM dbo.{table_name}) t"
        else:
            query = f"(SELECT * FROM dbo.{table_name}) t"

        df = (spark.read
            .format("jdbc")
            .option("url", JDBC_URL)
            .option("dbtable", query)
            .option("fetchsize", "1000")
            .load()
        )

        count = df.count()
        print(f"  ✅ Read {count} rows from [{table_name}]")

        if count > 0:
            # Lưu vào MinIO: s3a://raw-zone/pos/{table}/dt=YYYY-MM-DD/
            output_path = f"s3a://raw-zone/pos/{table_name}/dt={run_date}/"
            
            # Incremental thì append (chấp nhận trùng lặp ở Raw, sẽ khử trùng ở Silver)
            # Full load thì overwrite
            write_mode = "append" if mode == "incremental" else "overwrite"
            
            (df.coalesce(1)  # 1 file vì data nhỏ
               .write
               .mode(write_mode)
               .parquet(output_path))
            print(f"  ✅ Saved to {output_path} (mode={write_mode})")
        else:
            print(f"  ⚠️  No new rows for [{table_name}] — skipping write")

    finally:
        spark.stop()


# ─── DAG Definition ──────────────────────────────────────────────────────────
default_args = {
    "retries": 2,
    "retry_delay": timedelta(minutes=3),
    "owner": "tcmart-de",
}

with DAG(
    dag_id="dag_02_ingestion",
    description="Batch JDBC ingestion từ SQL Server → MinIO Raw Zone",
    start_date=datetime(2026, 1, 1),
    schedule_interval="0 * * * *",  # Mỗi giờ
    catchup=False,
    max_active_tasks=2,
    tags=["tcmart", "ingestion", "phase-3"],
    default_args=default_args,
) as dag:

    start = EmptyOperator(task_id="start")
    end   = EmptyOperator(task_id="end")

    # ── Nhóm 1: Giao dịch bán hàng — chạy mỗi giờ (incremental) ─────────────
    t_invoices = PythonOperator(
        task_id="ingest_sales_invoices",
        python_callable=run_spark_ingest,
        op_kwargs={
            "table_name": "sales_invoices",
            "mode": "incremental",
            "ts_column": "invoice_date",
            "lookback_hours": 2,
        },
    )

    t_items = PythonOperator(
        task_id="ingest_sales_invoice_items",
        python_callable=run_spark_ingest,
        op_kwargs={
            "table_name": "sales_invoice_items",
            "mode": "incremental",
            "custom_where": "invoice_id IN (SELECT invoice_id FROM dbo.sales_invoices WHERE invoice_date >= '{cutoff}')"
        },
    )

    t_tenders = PythonOperator(
        task_id="ingest_sales_payment_tenders",
        python_callable=run_spark_ingest,
        op_kwargs={
            "table_name": "sales_payment_tenders",
            "mode": "incremental",
            "custom_where": "invoice_id IN (SELECT invoice_id FROM dbo.sales_invoices WHERE invoice_date >= '{cutoff}')"
        },
    )

    # ── Nhóm 2: Dimension tables — chạy 1 lần/ngày ──────────────────────────
    t_products = PythonOperator(
        task_id="ingest_products",
        python_callable=run_spark_ingest,
        op_kwargs={"table_name": "products", "mode": "full"},
    )

    t_barcodes = PythonOperator(
        task_id="ingest_product_barcodes",
        python_callable=run_spark_ingest,
        op_kwargs={"table_name": "product_barcodes", "mode": "full"},
    )

    t_stores = PythonOperator(
        task_id="ingest_stores",
        python_callable=run_spark_ingest,
        op_kwargs={"table_name": "stores", "mode": "full"},
    )

    t_price_books = PythonOperator(
        task_id="ingest_store_price_books",
        python_callable=run_spark_ingest,
        op_kwargs={"table_name": "store_price_books", "mode": "full"},
    )

    # ── Nhóm 3: Ca kíp, Khách hàng, Tồn kho, Đổi trả ───────────────────────────────
    t_shifts = PythonOperator(
        task_id="ingest_cashier_shifts",
        python_callable=run_spark_ingest,
        op_kwargs={
            "table_name": "cashier_shifts",
            "mode": "incremental",
            "ts_column": "closed_at",
            "lookback_hours": 2,
        },
    )

    t_returns = PythonOperator(
        task_id="ingest_sales_returns",
        python_callable=run_spark_ingest,
        op_kwargs={
            "table_name": "sales_returns",
            "mode": "incremental",
            "ts_column": "return_timestamp",
            "lookback_hours": 2,
        },
    )
    
    t_customers = PythonOperator(
        task_id="ingest_customers",
        python_callable=run_spark_ingest,
        op_kwargs={
            "table_name": "customers",
            "mode": "incremental",
            "ts_column": "registered_at",
            "lookback_hours": 24, # Khách hàng mới cập nhật hàng ngày
        },
    )
    
    t_inventory = PythonOperator(
        task_id="ingest_inventory_snapshots",
        python_callable=run_spark_ingest,
        op_kwargs={
            "table_name": "store_inventory_snapshots",
            "mode": "incremental",
            "ts_column": "snapshot_date",
            "lookback_hours": 24, # Tồn kho ghi nhận hàng ngày
        },
    )

    # ── Dependency graph ─────────────────────────────────────────────────────
    # Dimensions trước
    start >> [t_products, t_barcodes, t_stores, t_price_books, t_customers]
    # Fact tables sau Dimensions
    [t_products, t_stores] >> t_invoices >> [t_items, t_tenders]
    [t_items, t_tenders] >> [t_shifts, t_returns, t_inventory] >> end
