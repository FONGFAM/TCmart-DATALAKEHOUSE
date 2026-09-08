"""
dag_03_silver.py — Airflow DAG (TODO: implement)
Tham khảo docs/04_data_flow.md để thiết kế logic.
"""
# pyrefly: ignore [missing-import]
from airflow import DAG
# pyrefly: ignore [missing-import]
from airflow.operators.empty import EmptyOperator
from datetime import datetime

with DAG(
    dag_id="dag_03_silver",
    start_date=datetime(2026, 1, 1),
    schedule_interval=None,
    catchup=False,
    max_active_tasks=2,   # ⚠️ Giữ tối đa 2 task song song (RAM constraint)
    tags=["tcmart"],
) as dag:
    start = EmptyOperator(task_id="start")
    end   = EmptyOperator(task_id="end")
    start >> end
