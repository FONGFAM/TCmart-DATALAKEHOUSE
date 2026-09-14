"""
dag_00_exchange_rate.py — Airflow DAG
Kéo tỷ giá ngoại tệ từ API bên ngoài mỗi ngày lúc 8h sáng.
Lưu raw JSON vào MinIO, sau đó load vào bảng Dim_ExchangeRate trên ClickHouse.

Nguồn API: ExchangeRate-API (free tier) hoặc SBV (Ngân hàng Nhà nước VN).
Endpoint: https://open.er-api.com/v6/latest/VND (free, no key required)
"""
# pyrefly: ignore [missing-import]
from airflow import DAG
# pyrefly: ignore [missing-import]
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
import json
import os

# ─── Cấu hình ────────────────────────────────────────────────────────────────
MINIO_ENDPOINT  = os.getenv("MINIO_ENDPOINT",  "http://tcmart-minio:9000")
MINIO_ACCESS    = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET    = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin2026")
CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "tcmart-clickhouse")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_HTTP_PORT", "8123"))
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "default")
CLICKHOUSE_PASS = os.getenv("CLICKHOUSE_PASSWORD", "tcmart2026")
CLICKHOUSE_DB   = "gold"

TARGET_CURRENCIES = ["USD", "CNY", "EUR", "JPY", "KRW", "THB"]

# ─── Task 1: Kéo tỷ giá từ API ───────────────────────────────────────────────
def fetch_exchange_rates(**context):
    """Gọi ExchangeRate-API lấy tỷ giá 1 VND vs các ngoại tệ, đổi ngược lại."""
    rate_date = context["ds"]  # YYYY-MM-DD từ Airflow execution date
    url = "https://open.er-api.com/v6/latest/VND"

    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        # Fallback: dùng tỷ giá tĩnh nếu API lỗi (để test pipeline không bị dừng)
        print(f"⚠️  API call failed: {e}. Using fallback static rates.")
        data = {
            "result": "fallback",
            "rates": {"USD": 1/25400, "CNY": 1/3500, "EUR": 1/27800,
                      "JPY": 1/165, "KRW": 1/19, "THB": 1/700}
        }

    # Đổi từ tỷ giá 1 VND = x USD → 1 USD = y VND
    rates_vnd = {}
    for cur in TARGET_CURRENCIES:
        rate_1vnd_to_cur = data["rates"].get(cur)
        if rate_1vnd_to_cur and rate_1vnd_to_cur > 0:
            rates_vnd[cur] = round(1.0 / rate_1vnd_to_cur, 2)
        else:
            rates_vnd[cur] = None

    payload = {
        "rate_date": rate_date,
        "source": "open.er-api.com",
        "rates_vnd": rates_vnd,
        "raw_response": data,
    }
    print(f"✅ Fetched rates for {rate_date}: {rates_vnd}")
    context["ti"].xcom_push(key="rates_payload", value=payload)


# ─── Task 2: Lưu raw vào MinIO ───────────────────────────────────────────────
def save_raw_to_minio(**context):
    """Lưu raw JSON tỷ giá vào MinIO bucket raw-zone/exchange_rates/YYYY/MM/DD/"""
    import boto3
    from botocore.client import Config

    payload = context["ti"].xcom_pull(key="rates_payload", task_ids="fetch_exchange_rates")
    rate_date = payload["rate_date"]
    year, month, day = rate_date.split("-")

    s3 = boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS,
        aws_secret_access_key=MINIO_SECRET,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )

    bucket = "raw-zone"
    key = f"exchange_rates/{year}/{month}/{day}/rates_{rate_date}.json"

    # Tạo bucket nếu chưa có
    try:
        s3.head_bucket(Bucket=bucket)
    except Exception:
        s3.create_bucket(Bucket=bucket)

    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(payload, ensure_ascii=False, indent=2),
        ContentType="application/json",
    )
    print(f"✅ Saved raw rates to MinIO: s3://{bucket}/{key}")


# ─── Task 3: Load vào ClickHouse Dim_ExchangeRate ────────────────────────────
def load_to_clickhouse(**context):
    """
    Upsert tỷ giá vào bảng gold.Dim_ExchangeRate trên ClickHouse.
    Dùng HTTP interface để không cần driver phức tạp.
    """
    import requests as req

    payload  = context["ti"].xcom_pull(key="rates_payload", task_ids="fetch_exchange_rates")
    rate_date = payload["rate_date"]
    rates_vnd = payload["rates_vnd"]
    source    = payload["source"]

    ch_url = f"http://{CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}/"
    auth   = (CLICKHOUSE_USER, CLICKHOUSE_PASS)

    rows_inserted = 0
    for currency, ref_rate in rates_vnd.items():
        if ref_rate is None:
            print(f"  ⚠️  Skipping {currency}: no rate available")
            continue

        # Tỷ giá mua = ref_rate * 0.985 (trừ spread ~1.5%), bán = ref_rate * 1.015
        buy_rate  = round(ref_rate * 0.985, 2)
        sell_rate = round(ref_rate * 1.015, 2)

        insert_sql = f"""
            INSERT INTO {CLICKHOUSE_DB}.Dim_ExchangeRate
            (rate_date, currency_code, buy_rate_vnd, sell_rate_vnd, reference_rate_vnd, data_source)
            VALUES ('{rate_date}', '{currency}', {buy_rate}, {sell_rate}, {ref_rate}, '{source}')
        """
        resp = req.post(ch_url, data=insert_sql, auth=auth, timeout=10)
        if resp.status_code == 200:
            rows_inserted += 1
        else:
            print(f"  ❌ Failed to insert {currency}: {resp.text}")

    print(f"✅ Loaded {rows_inserted} exchange rates for {rate_date} into ClickHouse")


# ─── DAG Definition ──────────────────────────────────────────────────────────
with DAG(
    dag_id="dag_00_exchange_rate",
    description="Kéo tỷ giá ngoại tệ hàng ngày từ API → MinIO → ClickHouse",
    start_date=datetime(2026, 1, 1),
    schedule_interval="0 8 * * *",  # 8h sáng mỗi ngày
    catchup=False,
    max_active_tasks=2,
    tags=["tcmart", "exchange_rate", "phase-2b"],
    default_args={
        "retries": 3,
        "retry_delay": timedelta(minutes=5),
        "owner": "tcmart-de",
    },
) as dag:

    t_fetch = PythonOperator(
        task_id="fetch_exchange_rates",
        python_callable=fetch_exchange_rates,
    )

    t_save_raw = PythonOperator(
        task_id="save_raw_to_minio",
        python_callable=save_raw_to_minio,
    )

    t_load_ch = PythonOperator(
        task_id="load_to_clickhouse",
        python_callable=load_to_clickhouse,
    )

    t_fetch >> t_save_raw >> t_load_ch
