"""
gen_production.py — Data Generator cho production_db (Oracle)
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


class ProductionGenerator(BaseGenerator):
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
        print("Generating data for production_db (Oracle)...")
        products, employees = self.get_master_data()
        if not products or not employees:
            print("❌ Lỗi: Cần chạy gen_product.py và gen_employee.py trước!")
            return

        with self.engine.connect() as conn:
            conn.execute(text("DELETE FROM material_consumptions"))
            conn.execute(text("DELETE FROM production_order_items"))
            conn.execute(text("DELETE FROM raw_materials"))
            conn.execute(text("DELETE FROM finished_products"))
            conn.execute(text("DELETE FROM production_orders"))
            conn.execute(text("DELETE FROM factories"))
            conn.commit()
        
        with self.get_session() as session:
            # 1. Factories
            factory_ids = []
            for i in range(1, 4): # 3 nhà máy
                session.execute(
                    text("""
                        INSERT INTO factories (factory_code, factory_name, region, address, capacity, status)
                        VALUES (:code, :name, :region, :loc, :cap, 'active')
                    """),
                    {
                        "code": f"FAC-{i:03d}",
                        "name": f"Nhà máy Sản xuất {i}",
                        "region": random.choice(["North", "Central", "South"]),
                        "loc": self.fake.address(),
                        "cap": random.randint(10000, 50000)
                    }
                )
            session.commit()
            
            res = session.execute(text("SELECT factory_id FROM factories"))
            factory_ids = [r[0] for r in res.fetchall()]
            print(f" - Inserted {len(factory_ids)} factories.")

            # 2. Raw Materials
            material_ids = []
            for i in range(1, 51):
                session.execute(
                    text("""
                        INSERT INTO raw_materials (material_code, material_name, unit)
                        VALUES (:code, :name, :unit)
                    """),
                    {
                        "code": f"RM-{i:03d}",
                        "name": f"Nguyên liệu {self.fake.word().capitalize()}",
                        "unit": random.choice(["kg", "lit", "m", "pcs"])
                    }
                )
            session.commit()
            res_mat = session.execute(text("SELECT material_id FROM raw_materials"))
            material_ids = [r[0] for r in res_mat.fetchall()]

            # 3. Production Orders
            num_orders = GEN_CONFIG.get("num_production_orders", 200)
            for i in range(1, num_orders + 1):
                start_date = self.fake.date_time_this_year()
                end_date = start_date + timedelta(days=random.randint(2, 10))
                target_qty = random.randint(1000, 5000)
                produced_qty = target_qty if random.random() > 0.1 else int(target_qty * 0.9)
                fg_pid = random.choice(products)
                fac_id = random.choice(factory_ids)
                emp_id = random.choice(employees)

                # insert production order
                session.execute(
                    text("""
                        INSERT INTO production_orders (production_order_number, factory_id, product_id, employee_id, planned_quantity, actual_quantity, start_date, end_date, status)
                        VALUES (:num, :fac, :pid, :eid, :tqty, :pqty, :startd, :endd, :status)
                    """),
                    {
                        "num": f"PROD-{start_date.strftime('%Y%m%d')}-{i:04d}",
                        "fac": fac_id,
                        "pid": fg_pid,
                        "eid": emp_id,
                        "tqty": target_qty,
                        "pqty": produced_qty,
                        "startd": start_date,
                        "endd": end_date,
                        "status": random.choice(["Completed", "In Progress", "Planned"])
                    }
                )
            session.commit()
            
            # Fetch all orders to insert items, consumption, finished
            res_orders = session.execute(text("SELECT production_order_id, product_id, actual_quantity FROM production_orders WHERE status = 'Completed'"))
            orders = res_orders.fetchall()
            
            for order in orders:
                oid = order[0]
                pid = order[1]
                qty = order[2]
                
                # finished products
                session.execute(
                    text("""
                        INSERT INTO finished_products (production_order_id, product_id, quantity, warehouse_id)
                        VALUES (:oid, :pid, :qty, 1)
                    """),
                    {"oid": oid, "pid": pid, "qty": qty}
                )

                # production order items & material consumption
                order_materials = random.sample(material_ids, k=random.randint(1, 5))
                for mat_id in order_materials:
                    req_qty = qty * random.uniform(0.1, 2.0)
                    act_qty = req_qty * random.uniform(0.9, 1.1)
                    session.execute(
                        text("""
                            INSERT INTO production_order_items (production_order_id, material_id, plan, ned_quantity, actual_quantity)
                            VALUES (:oid, :mid, 'Plan A', :req, :act)
                        """),
                        {"oid": oid, "mid": mat_id, "req": req_qty, "act": act_qty}
                    )
                    
                    session.execute(
                        text("""
                            INSERT INTO material_consumptions (production_order_id, material_id, employee_id, quantity)
                            VALUES (:oid, :mid, :eid, :act)
                        """),
                        {"oid": oid, "mid": mat_id, "eid": random.choice(employees), "act": act_qty}
                    )

            session.commit()
            print(f" - Inserted {num_orders} production orders and related records.")


if __name__ == "__main__":
    generator = ProductionGenerator()
    generator.run()
