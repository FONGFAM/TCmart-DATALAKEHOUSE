"""
dag_03_silver_transform.py — Airflow DAG
Trigger PySpark Silver transformation mỗi giờ, sau khi ingestion hoàn thành.
"""
# pyrefly: ignore [missing-import]
from airflow import DAG
# pyrefly: ignore [missing-import]
from airflow.operators.python import PythonOperator
# pyrefly: ignore [missing-import]
from airflow.operators.empty import EmptyOperator
# pyrefly: ignore [missing-import]
from airflow.sensors.external_task import ExternalTaskSensor
from datetime import datetime, timedelta
import subprocess
import os

SPARK_SUBMIT = os.getenv("SPARK_SUBMIT_BIN", "spark-submit")
SILVER_JOB   = "/opt/airflow/dags/../../../src/processing/silver_transform.py"


def run_silver_transform(**context):
    run_date = context["ds"]
    print(f"⏳ Running Silver transform for {run_date}...")
    result = subprocess.run(
        [SPARK_SUBMIT,
         "--master", "local[2]",
         "--driver-memory", "512m",
         "--executor-memory", "512m",
         SILVER_JOB, run_date],
        capture_output=True, text=True, timeout=600
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError(f"Silver transform failed: {result.stderr[-500:]}")
    print(f"✅ Silver transform completed for {run_date}")


with DAG(
    dag_id="dag_03_silver_transform",
    description="PySpark Silver transformation: DQ + Shift Reconciliation + Sales Line Items",
    start_date=datetime(2026, 1, 1),
    schedule_interval="30 * * * *",  # 30 phút sau ingestion
    catchup=False,
    max_active_tasks=1,  # Không chạy song song — tránh OOM
    tags=["tcmart", "silver", "phase-3"],
    default_args={
        "retries": 1,
        "retry_delay": timedelta(minutes=10),
        "owner": "tcmart-de",
    },
) as dag:

    # Chờ ingestion DAG chạy xong
    wait_ingestion = ExternalTaskSensor(
        task_id="wait_for_ingestion",
        external_dag_id="dag_02_ingestion",
        external_task_id="end",
        timeout=3600,
        poke_interval=60,
        mode="poke",
    )

    t_silver = PythonOperator(
        task_id="run_silver_transform",
        python_callable=run_silver_transform,
    )

    wait_ingestion >> t_silver
