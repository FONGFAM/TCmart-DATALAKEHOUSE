.PHONY: help up-sources up-oracle up-streaming up-lakehouse up-bi \
        down-sources down-streaming down-lakehouse down-bi down-all \
        ram-check gen-all gen-dirty test spark-build setup

# ── Màu sắc terminal ──────────────────────────────────────────────────────────
GREEN  := \033[0;32m
YELLOW := \033[0;33m
RED    := \033[0;31m
NC     := \033[0m

# ── Đường dẫn ─────────────────────────────────────────────────────────────────
INFRA_DIR   := infra
SRC_DIR     := src
VENV        := .venv
PYTHON      := python3.10

help: ## Hiển thị danh sách lệnh
	@echo ""
	@echo "$(GREEN)TCmart-DATALAKEHOUSE — Available Commands$(NC)"
	@echo "────────────────────────────────────────────"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

# ── RAM Check ─────────────────────────────────────────────────────────────────
ram-check: ## Kiểm tra RAM khả dụng hiện tại
	@echo "$(GREEN)🔍 RAM khả dụng:$(NC)"
	@vm_stat | grep "Pages free" | awk '{printf "   %.0f MB free\n", $$3 * 4096 / 1024 / 1024}'
	@echo ""
	@docker stats --no-stream --format "   {{.Name}}: {{.MemUsage}}" 2>/dev/null || true

# ── Docker — Phased Startup ───────────────────────────────────────────────────
up-sources: ram-check ## [PHASE 1] Bật Source DBs: MSSQL + Postgres + MinIO (~4 GB)
	@echo "$(GREEN)🚀 Khởi động Source Databases...$(NC)"
	@cp -n $(INFRA_DIR)/.env.example $(INFRA_DIR)/.env 2>/dev/null || true
	docker compose -f $(INFRA_DIR)/sources/docker-compose.yml \
		--env-file $(INFRA_DIR)/.env \
		--profile sources up -d
	@echo "$(GREEN)✅ Source DBs đang khởi động. Chờ ~60s để MSSQL sẵn sàng.$(NC)"

up-oracle: ## [PHASE 1+] Bật Oracle XE (nặng ~2 GB — chỉ bật khi cần!)
	@echo "$(RED)⚠️  Oracle XE sẽ dùng thêm ~2GB RAM!$(NC)"
	@make ram-check
	docker compose -f $(INFRA_DIR)/sources/docker-compose.yml \
		--env-file $(INFRA_DIR)/.env \
		--profile oracle up -d oracle-source

up-streaming: ## [PHASE 2] Bật Kafka + Spark (~3 GB thêm)
	@echo "$(GREEN)🚀 Khởi động Streaming Layer...$(NC)"
	docker compose -f $(INFRA_DIR)/streaming/docker-compose.yml up -d
	@echo "$(GREEN)✅ Kafka UI: http://localhost:29092 | Spark UI: http://localhost:8090$(NC)"

up-lakehouse: ## [PHASE 3] Bật ClickHouse + Airflow + FastAPI (~3.5 GB thêm)
	@echo "$(GREEN)🚀 Khởi động Lakehouse Layer...$(NC)"
	docker compose -f $(INFRA_DIR)/lakehouse/docker-compose.yml \
		--env-file $(INFRA_DIR)/.env up -d
	@echo "$(GREEN)✅ Airflow UI: http://localhost:8080 | ClickHouse: http://localhost:8123$(NC)"
	@echo "$(GREEN)✅ Data Steward API: http://localhost:8000/docs$(NC)"

up-bi: ## [PHASE 4] Bật Superset (~768 MB thêm)
	@echo "$(YELLOW)⚠️  Nhớ tắt Spark trước nếu RAM < 5GB free!$(NC)"
	@make ram-check
	docker compose -f $(INFRA_DIR)/bi/docker-compose.yml \
		--env-file $(INFRA_DIR)/.env up -d
	@echo "$(GREEN)✅ Superset UI: http://localhost:8088 (admin/admin)$(NC)"

# ── Docker — Shutdown ─────────────────────────────────────────────────────────
down-sources: ## Tắt Source DBs
	docker compose -f $(INFRA_DIR)/sources/docker-compose.yml --profile sources down

down-oracle: ## Tắt chỉ Oracle XE (giải phóng 2GB RAM)
	docker compose -f $(INFRA_DIR)/sources/docker-compose.yml stop oracle-source

down-streaming: ## Tắt Kafka + Spark
	docker compose -f $(INFRA_DIR)/streaming/docker-compose.yml down

down-lakehouse: ## Tắt ClickHouse + Airflow + FastAPI
	docker compose -f $(INFRA_DIR)/lakehouse/docker-compose.yml down

down-bi: ## Tắt Superset
	docker compose -f $(INFRA_DIR)/bi/docker-compose.yml down

down-all: ## Tắt toàn bộ stack
	@echo "$(RED)🛑 Tắt toàn bộ TCmart stack...$(NC)"
	-docker compose -f $(INFRA_DIR)/sources/docker-compose.yml --profile sources --profile oracle down
	-docker compose -f $(INFRA_DIR)/streaming/docker-compose.yml down
	-docker compose -f $(INFRA_DIR)/lakehouse/docker-compose.yml down
	-docker compose -f $(INFRA_DIR)/bi/docker-compose.yml down
	@echo "$(GREEN)✅ Tất cả services đã dừng.$(NC)"

# ── Python Environment ────────────────────────────────────────────────────────
setup: ## Tạo virtual environment Python 3.10 và cài dependencies
	@echo "$(GREEN)🐍 Tạo virtual environment bằng Python 3.10...$(NC)"
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r $(SRC_DIR)/generator/requirements.txt
	@echo "$(GREEN)✅ Virtual environment sẵn sàng. Activate: source .venv/bin/activate$(NC)"

# ── Data Generator ────────────────────────────────────────────────────────────
gen-all: ## Sinh dữ liệu mẫu cho toàn bộ 12 DBs (≤10,000 records/table)
	@echo "$(GREEN)🎲 Sinh dữ liệu mẫu...$(NC)"
	$(VENV)/bin/python $(SRC_DIR)/generator/main.py --db all

gen-dirty: ## Nhồi ~5% dữ liệu lỗi có chủ đích (test Data Quality)
	@echo "$(YELLOW)⚠️  Đang nhồi dữ liệu lỗi cho mục đích test...$(NC)"
	$(VENV)/bin/python $(SRC_DIR)/generator/dirty/inject_errors.py

# ── Tests ─────────────────────────────────────────────────────────────────────
test: ## Chạy unit tests
	$(VENV)/bin/pytest tests/unit/ -v

test-integration: ## Chạy integration tests (cần sources đang up)
	$(VENV)/bin/pytest tests/integration/ -v

# ── Spark Build ───────────────────────────────────────────────────────────────
spark-build: ## Build Spark Java jobs bằng Maven
	@echo "$(GREEN)☕ Building Spark jobs with Maven...$(NC)"
	cd $(SRC_DIR)/processing && mvn clean package -DskipTests
	@echo "$(GREEN)✅ JAR files created in src/processing/target/$(NC)"

# ── Docker Cleanup ────────────────────────────────────────────────────────────
docker-clean: ## Dọn dẹp Docker build cache (giải phóng disk)
	docker builder prune -f
	@echo "$(GREEN)✅ Docker build cache đã được dọn dẹp.$(NC)"
