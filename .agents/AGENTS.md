# Workspace Rules: TCmart-DATALAKEHOUSE

These rules govern the behavior of the AI Agent (Antigravity) while working in this specific repository.

## 1. System Environment (macOS Focus)
- **OS**: Always assume the host environment is **macOS (Intel x86_64)**.
- **Shell**: Use `zsh` conventions for any shell commands.
- **Package Management**: Recommend or use `brew` (Homebrew) for installing dependencies if they are missing on the host.
- **Python**: Always use `python3.10` to create virtual environments (`python3.10 -m venv .venv`). Do NOT use the default `python3` (which is 3.9 on this host). Ensure the virtual environment is activated before running any python scripts or installing `pip` packages.
- **Java**: The host uses Java 17 via `/Library/Java/JavaVirtualMachines/jdk-17.0.20.1.jdk`. Ensure `JAVA_HOME` is set appropriately when executing Spark, NiFi, or Airflow locally outside Docker.
- **Paths**: Use macOS forward slash (`/`) paths. 

## 2. Project Architecture & Standards
- **Core Stack**: ClickHouse (Lakehouse), Airflow (Orchestrator), Spark & NiFi (Ingestion/Streaming), PostgreSQL/MSSQL/Oracle (Sources), FastAPI (Data Steward), Superset (BI).
- **Medallion Architecture**: Strictly adhere to the Bronze -> Silver -> Gold data layers when building pipelines.
- **Infrastructure**: All databases and services should be orchestrated via `Docker Compose`. Containers should communicate using container names. When the host needs to connect to a container, use `localhost`.
- **SQL Dialects**: Be extremely careful to use the correct SQL dialect based on the target engine:
  - `retail_pos_db`: **T-SQL** (Microsoft SQL Server).
  - `procurement_db`, `warehouse_db`, `production_db`: **PL/SQL** (Oracle).
  - `ecommerce_db`, `employee_db`, `franchise_db` (and others): **PostgreSQL**.
  - Analytics Layers: **ClickHouse SQL**.

## 3. Workflow Guidelines
1. **Always Consult `plan.md`**: Before starting a new task, verify its position within the 15-step `plan.md`. Do not skip ahead unless the user explicitly requests it.
2. **Review Data Dictionary**: Always refer to `docs/01_source_data_dictionary.md` for accurate table names, column data types, and primary/foreign keys. Do not hallucinate table structures.
3. **Plan Before Execution**: For any major architectural changes (e.g., creating a new pipeline, defining a new set of Docker containers), write an `implementation_plan.md` artifact and ask for user approval before writing code.
4. **Iterative Development**: Write code in small, testable chunks. For example, write the data generator, test it, and verify the output before moving to the Airflow DAG.
5. **Data Quality First**: When generating mock data, intentionally include edge cases (nulls, duplicates, invalid formats) to ensure the Data Quality pipelines (Great Expectations) can be thoroughly tested.

## 4. Communication & Actions
- **Conciseness**: Keep responses brief and focused on the technical implementation. Avoid repetitive pleasantries.
- **Language**: Communicate primarily in Vietnamese (unless technical terms are better left in English).
- **Destructive Actions**: ALWAYS ask for user confirmation before dropping databases, deleting large amounts of data, or running destructive Git commands (e.g., `git reset --hard`).

## 5. Resource Constraints — Low-Spec Machine Rules (16 GB RAM, Intel x86_64)

> ⚠️ CRITICAL: The host machine has only **16 GB RAM**. Running all services simultaneously WILL crash the system.
> Every Docker service definition MUST include explicit memory limits. Never omit `mem_limit` or `mem_reservation`.

### 5.1 Docker Memory Budget (Total ≤ 12 GB usable for containers)

| Service | Image | mem_limit | mem_reservation | Ghi chú |
|---|---|---|---|---|
| **mssql-source** | `mssql/server:2022-latest` | `1.5g` | `1g` | Source DB |
| **postgres-source** | `postgres:15-alpine` | `512m` | `256m` | Source DB (nhiều schema) |
| **oracle-source** | `gvenzl/oracle-xe:21-slim` | `2g` | `1.5g` | Nặng nhất — chỉ bật khi test Oracle |
| **minio** | `minio/minio` | `512m` | `256m` | Object storage |
| **kafka** + **zookeeper** | Confluent | `1g` | `512m` | Cộng gộp cả 2 |
| **spark-master** | Bitnami Spark | `1g` | `512m` | |
| **spark-worker** | Bitnami Spark | `1.5g` | `1g` | Chỉ 1 worker duy nhất |
| **clickhouse** | `clickhouse-server:24.3` | `1.5g` | `1g` | |
| **airflow** | `apache/airflow:2.9` | `1g` | `512m` | |
| **superset** | `apache/superset` | `768m` | `512m` | |
| **fastapi** (data-steward) | Custom Python | `256m` | `128m` | |

### 5.2 Phased Startup Strategy — NEVER start all services at once

Tuyệt đối KHÔNG được viết lệnh `docker compose up -d` khởi động toàn bộ stack. Luôn dùng Docker Compose Profiles để khởi động theo pha:

```bash
# Pha 1 — Chỉ Source DBs (khi viết DDL, chạy generator)
docker compose --profile sources up -d
# RAM tiêu thụ: ~4 GB

# Pha 2 — Thêm Kafka + Spark (khi test ingestion pipeline)
docker compose --profile streaming up -d
# RAM tiêu thụ: ~7 GB

# Pha 3 — Thêm ClickHouse + Airflow (khi test Bronze/Silver/Gold)
docker compose --profile lakehouse up -d
# RAM tiêu thụ: ~10 GB

# Pha 4 — Thêm Superset (chỉ khi demo BI)
docker compose --profile bi up -d
# RAM tiêu thụ: ~11 GB
```

### 5.3 Oracle XE — Chỉ bật khi cần thiết

Oracle XE chiếm ~2 GB RAM ngay khi khởi động. Khi không test Oracle-specific features:
- Dùng PostgreSQL schema (`oracle_compat`) để thay thế trong quá trình phát triển.
- Chỉ bật Oracle container khi cần kiểm thử PL/SQL syntax hoặc JDBC connector.
- Sau khi test xong, **luôn tắt ngay**: `docker compose stop oracle-source`.

### 5.4 Spark Configuration — Giới hạn tài nguyên

Khi viết bất kỳ Spark job nào (Java hoặc PySpark), LUÔN đặt các cấu hình sau:
```python
spark = SparkSession.builder \
    .config("spark.executor.memory", "512m") \
    .config("spark.driver.memory", "512m") \
    .config("spark.executor.cores", "1") \
    .config("spark.sql.shuffle.partitions", "4") \  # Mặc định là 200 — phải override
    .getOrCreate()
```

### 5.5 Forbidden Patterns (Cấm tuyệt đối)

- ❌ Không viết `docker compose up` không có `--profile` khi toàn bộ stack chưa được kiểm tra RAM.
- ❌ Không để `spark.sql.shuffle.partitions` ở giá trị mặc định (200).
- ❌ Không chạy Spark job local với nhiều hơn 2 cores: `spark.master = local[2]` là tối đa.
- ❌ Không chạy đồng thời Oracle + Kafka + Spark + Superset.
- ❌ Không tạo Airflow DAG chạy nhiều task song song (max `max_active_tasks = 2`).
- ❌ Không sinh dữ liệu Generator với số lượng > 10,000 bản ghi mỗi lần chạy để tránh OOM.

### 5.6 Kiểm tra RAM trước khi khởi động service nặng

Trước khi hướng dẫn anh/chị bật Oracle, Spark, hoặc Kafka, agent PHẢI kiểm tra RAM khả dụng:
```bash
vm_stat | grep "Pages free" | awk '{print $3 * 4096 / 1024 / 1024 " MB free"}'
```
Nếu RAM khả dụng < 3 GB, DỪNG LẠI và yêu cầu anh/chị tắt bớt service trước.
