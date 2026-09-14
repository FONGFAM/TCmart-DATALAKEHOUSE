#!/bin/bash
set -e

echo "Starting Superset initialization..."

# Cài đặt ClickHouse driver
echo "Installing clickhouse-connect..."
pip install clickhouse-connect==0.7.3

# Initialize the database
echo "Upgrading DB..."
superset db upgrade

# Create an admin user if it doesn't exist
echo "Creating admin user..."
superset fab create-admin \
    --username "$ADMIN_USERNAME" \
    --firstname Superset \
    --lastname Admin \
    --email "$ADMIN_EMAIL" \
    --password "$ADMIN_PASSWORD" || true

# Create default roles and permissions
echo "Initializing Superset roles..."
superset init

# Bổ sung Database Connection (Tự động cắm vào ClickHouse)
# Lưu ý: superset set_database_uri yêu cầu CLI > 3.0
echo "Adding ClickHouse Database connection..."
superset set_database_uri \
    -d ClickHouse_Mart \
    -u clickhouse+native://default:tcmart2026@tcmart-clickhouse:9000/mart || true

echo "Starting Superset server..."
gunicorn -w 2 --timeout 120 -b  0.0.0.0:8088 --limit-request-line 0 --limit-request-field_size 0 "superset.app:create_app()"