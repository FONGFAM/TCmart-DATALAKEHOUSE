"""
dag_04_gold_load.py — Airflow DAG
Trigger PySpark Gold Load job mỗi ngày lúc 2h sáng.
Chạy sau khi Silver transformation của ngày hôm trước hoàn tất.
"""
# pyrefly: ignore [missing-import]
from airflow import DAG
# pyrefly: ignore [missing-import]
from airflow.operators.python import PythonOperator
# pyrefly: ignore [missing-import]
from airflow.operators.empty import EmptyOperator
from datetime import datetime, timedelta
import subprocess
import os

SPARK_SUBMIT = os.getenv("SPARK_SUBMIT_BIN", "spark-submit")
GOLD_JOB     = "/opt/airflow/dags/../../../src/processing/gold_load.py"
DIM_DATE_JOB = "/opt/airflow/dags/../../../src/processing/populate_dim_date.py"


def run_gold_load(**context):
    run_date = context["ds"]
    print(f"⏳ Running Gold load for {run_date}...")
    result = subprocess.run(
        [SPARK_SUBMIT,
         "--master", "local[2]",
         "--driver-memory", "512m",
         "--executor-memory", "512m",
         "--jars", "/opt/spark/jars/clickhouse-jdbc-0.6.1-all.jar",
         GOLD_JOB, run_date],
        capture_output=True, text=True, timeout=1200
    )
    print(result.stdout[-3000:])
    if result.returncode != 0:
        print(result.stderr[-500:])
        raise RuntimeError("Gold load failed")
    print(f"✅ Gold load completed for {run_date}")


def check_dim_date_seeded(**context):
    """Kiểm tra Dim_Date đã được seed chưa. Nếu chưa, seed luôn."""
    import requests
    url = f"http://{os.getenv('CLICKHOUSE_HOST','tcmart-clickhouse')}:8123/"
    auth = (os.getenv("CLICKHOUSE_USER","default"), os.getenv("CLICKHOUSE_PASSWORD","tcmart2026"))
    r = requests.post(url, data="SELECT count() FROM gold.Dim_Date FORMAT JSONCompact", auth=auth, timeout=10)
    count = 0
    if r.status_code == 200:
        count = int(r.json()["data"][0][0])

    if count < 100:
        print(f"⚠️  Dim_Date chỉ có {count} rows — cần seed. Chạy populate_dim_date.py...")
        result = subprocess.run(
            ["python3", DIM_DATE_JOB],
            capture_output=True, text=True, timeout=300
        )
        if result.returncode != 0:
            raise RuntimeError(f"Dim_Date seed failed: {result.stderr}")
        print("✅ Dim_Date seeded")
    else:
        print(f"✅ Dim_Date OK: {count} rows")


with DAG(
    dag_id="dag_04_gold_load",
    description="Load Silver Zone → ClickHouse Gold (Dims + Facts)",
    start_date=datetime(2026, 1, 1),
    schedule_interval="0 2 * * *",   # 2h sáng mỗi ngày
    catchup=False,
    max_active_tasks=1,
    tags=["tcmart", "gold", "phase-4"],
    default_args={
        "retries": 1,
        "retry_delay": timedelta(minutes=15),
        "owner": "tcmart-de",
    },
) as dag:

    start = EmptyOperator(task_id="start")
    end   = EmptyOperator(task_id="end")

    t_check_dim_date = PythonOperator(
        task_id="ensure_dim_date_seeded",
        python_callable=check_dim_date_seeded,
    )

    t_gold_load = PythonOperator(
        task_id="run_gold_load",
        python_callable=run_gold_load,
    )

    start >> t_check_dim_date >> t_gold_load >> end
