"""
gen_warehouse.py — Data Generator cho warehouse_db (Oracle)
Phụ thuộc: product_db (lấy product_id), employee_db (lấy employee_id)
"""
import sys
import os
import random
from sqlalchemy import text
from datetime import timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import ORACLE_URL, PG_BASE_URL, GEN_CONFIG
from generators.base import BaseGenerator
from sqlalchemy import create_engine


class WarehouseGenerator(BaseGenerator):
    def __init__(self):
        super().__init__(ORACLE_URL)
        self.pg_engine = create_engine(PG_BASE_URL.format(db="postgres"))

    def get_master_data(self):
        product_ids = []
        employee_ids = []
        with self.pg_engine.connect() as conn:
            res_prod = conn.execute(text("SELECT product_id FROM product_db.products WHERE status='active'"))
            product_ids = [r[0] for r in res_prod.fetchall()]
            
            res_emp = conn.execute(text("SELECT employee_id FROM employee_db.employees WHERE status='active'"))
            employee_ids = [r[0] for r in res_emp.fetchall()]
            
        return product_ids, employee_ids

    def run(self):
        print("Generating data for warehouse_db (Oracle)...")
        products, employees = self.get_master_data()
        if not products or not employees:
            print("❌ Lỗi: Cần chạy gen_product.py và gen_employee.py trước!")
            return

        with self.engine.connect() as conn:
            conn.execute(text("DELETE FROM stock_transfer_items"))
            conn.execute(text("DELETE FROM stock_transfers"))
            conn.execute(text("DELETE FROM inventory_transactions"))
            conn.execute(text("DELETE FROM inventory"))
            conn.execute(text("DELETE FROM warehouse_locations"))
            conn.execute(text("DELETE FROM warehouses"))
            conn.commit()
        
        with self.get_session() as session:
            # 1. Warehouses
            warehouse_ids = []
            for i in range(1, 6): # 5 warehouses
                session.execute(
                    text("""
                        INSERT INTO warehouses (warehouse_code, warehouse_name, warehouse_type, region, address, capacity, status)
                        VALUES (:code, :name, 'Distribution', :region, :loc, :cap, 'active')
                    """),
                    {
                        "code": f"WH-{i:03d}",
                        "name": f"Kho Tổng {self.fake.city()}",
                        "region": random.choice(["North", "Central", "South"]),
                        "loc": self.fake.address(),
                        "cap": random.randint(10000, 50000)
                    }
                )
            session.commit()
            
            res = session.execute(text("SELECT warehouse_id FROM warehouses"))
            warehouse_ids = [r[0] for r in res.fetchall()]
            print(f" - Inserted {len(warehouse_ids)} warehouses.")

            # 2. Locations, Inventory & Transactions
            for wid in warehouse_ids:
                # Create some locations for this warehouse
                loc_ids = []
                for j in range(1, 6):
                    session.execute(
                        text("""
                            INSERT INTO warehouse_locations (warehouse_id, location_code, location_name, zone)
                            VALUES (:wid, :code, :name, :zone)
                        """),
                        {
                            "wid": wid,
                            "code": f"LOC-{wid}-{j:02d}",
                            "name": f"Location {j}",
                            "zone": random.choice(["A", "B", "C"])
                        }
                    )
                session.commit()
                res_loc = session.execute(text("SELECT location_id FROM warehouse_locations WHERE warehouse_id = :wid"), {"wid": wid})
                loc_ids = [r[0] for r in res_loc.fetchall()]

                # Assign products
                wh_products = random.sample(products, k=min(50, len(products)))
                for pid in wh_products:
                    qty = random.randint(100, 5000)
                    lid = random.choice(loc_ids)
                    
                    session.execute(
                        text("""
                            INSERT INTO inventory (warehouse_id, location_id, product_id, quantity, reserved_quantity, available_quantity)
                            VALUES (:wid, :lid, :pid, :qty, 0, :qty)
                        """),
                        {
                            "wid": wid, "lid": lid, "pid": pid, "qty": qty
                        }
                    )
                    
                    # 3. Movements
                    session.execute(
                        text("""
                            INSERT INTO inventory_transactions (warehouse_id, product_id, transaction_type, reference_type, reference_id, quantity, employee_id, transaction_date)
                            VALUES (:wid, :pid, 'IN', 'INIT', 0, :qty, :eid, :date)
                        """),
                        {
                            "wid": wid, "pid": pid, "qty": qty,
                            "eid": random.choice(employees),
                            "date": self.fake.date_time_this_year()
                        }
                    )
            
            session.commit()
            print(" - Inserted inventory and stock movements.")


if __name__ == "__main__":
    generator = WarehouseGenerator()
    generator.run()
