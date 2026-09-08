"""
main.py — Script chính điều phối việc chạy toàn bộ Data Generators
Thứ tự chạy:
1. Master Data (Độc lập)
2. Core Systems (Phụ thuộc Master)
3. Derived Systems (Phụ thuộc Core)
"""
import os
import sys
import subprocess

def run_script(script_name):
    print(f"\n{'='*50}")
    print(f"🚀 Running: {script_name}")
    print(f"{'='*50}")
    script_path = os.path.join(os.path.dirname(__file__), "generators", script_name)
    if not os.path.exists(script_path):
        print(f"⚠️ Script {script_name} không tồn tại. Bỏ qua.")
        return True
        
    result = subprocess.run([sys.executable, script_path])
    if result.returncode != 0:
        print(f"❌ Lỗi khi chạy {script_name}")
        return False
    return True

def main():
    print("Bắt đầu quy trình sinh dữ liệu giả lập Data Lakehouse...\n")
    
    # 1. Nhóm Master Data (Không phụ thuộc, có thể chạy song song)
    master_scripts = [
        "gen_exchange_rate.py",
        "gen_product.py",
        "gen_employee.py"
    ]
    
    # 2. Nhóm Core Systems (Phụ thuộc Master Data)
    core_scripts = [
        "gen_ecommerce.py",     # Postgres
        "gen_franchise.py",     # Postgres
        "gen_retail_pos.py",    # SQL Server
        "gen_promotion.py",     # Postgres
        "gen_marketing.py",     # Postgres
        "gen_procurement.py",   # Oracle
        "gen_warehouse.py",     # Oracle
        "gen_production.py"     # Oracle
    ]
    
    # 3. Nhóm Derived Systems (Phụ thuộc Core Systems)
    derived_scripts = [
        "gen_invoice.py",
    ]
    
    print("--- 1. MASTER DATA ---")
    for script in master_scripts:
        if not run_script(script): return
        
    print("\n--- 2. CORE SYSTEMS ---")
    for script in core_scripts:
        if not run_script(script): return
        
    print("\n--- 3. DERIVED SYSTEMS ---")
    for script in derived_scripts:
        if not run_script(script): return
        
    print("\n✅ TẤT CẢ DATA GENERATORS ĐÃ CHẠY THÀNH CÔNG!")

if __name__ == "__main__":
    main()
