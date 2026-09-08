import sys
import os
import random
from sqlalchemy import text
from datetime import timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import PG_BASE_URL, GEN_CONFIG
from generators.base import BaseGenerator
from sqlalchemy import create_engine

class PromotionGenerator(BaseGenerator):
    def __init__(self):
        super().__init__(PG_BASE_URL.format(db="postgres") + "?options=-c%20search_path=promotion_db")
        self.pg_engine = create_engine(PG_BASE_URL.format(db="postgres"))

    def get_master_data(self):
        product_ids = []
        employee_ids = []
        store_ids = []
        with self.pg_engine.connect() as conn:
            res_prod = conn.execute(text("SELECT product_id FROM product_db.products WHERE status='active'"))
            product_ids = [r[0] for r in res_prod.fetchall()]
            
            res_emp = conn.execute(text("SELECT employee_id FROM employee_db.employees WHERE status='active'"))
            employee_ids = [r[0] for r in res_emp.fetchall()]
            
            res_store = conn.execute(text("SELECT franchisee_id FROM franchise_db.franchisees WHERE status='active'"))
            store_ids = [r[0] for r in res_store.fetchall()]
        return product_ids, employee_ids, store_ids

    def run(self):
        print("Generating data for promotion_db...")
        product_ids, employee_ids, store_ids = self.get_master_data()
        if not product_ids or not employee_ids:
            print("❌ Lỗi: Cần chạy gen_product.py, gen_employee.py trước!")
            return

        self.truncate_table("promotion_discounts")
        self.truncate_table("promotion_stores")
        self.truncate_table("promotion_products")
        self.truncate_table("promotions")
        
        with self.get_session() as session:
            num_promos = GEN_CONFIG.get("num_promotions", 50)
            promo_ids = []
            for i in range(1, num_promos + 1):
                start_date = self.fake.date_time_this_year()
                end_date = start_date + timedelta(days=random.randint(5, 30))
                
                res = session.execute(
                    text("""
                        INSERT INTO promotions (promotion_code, promotion_name, promotion_type, employee_id, start_date, end_date, status)
                        VALUES (:code, :name, :type, :emp, :start, :end, :status)
                        RETURNING promotion_id
                    """),
                    {
                        "code": f"PROMO-{i:03d}-{start_date.strftime('%m%y')}",
                        "name": f"Chương trình {self.fake.word()} {start_date.strftime('%B')}",
                        "type": random.choice(["FlashSale", "Holiday", "Clearance", "MemberOnly"]),
                        "emp": random.choice(employee_ids),
                        "start": start_date,
                        "end": end_date,
                        "status": random.choice(["Active", "Expired", "Upcoming"])
                    }
                )
                promo_id = res.scalar()
                
                # promotion_products
                if random.random() > 0.3:  # 70% promos are product specific
                    promo_prods = random.sample(product_ids, k=min(len(product_ids), random.randint(5, 20)))
                    for pid in promo_prods:
                        session.execute(text("INSERT INTO promotion_products (promotion_id, product_id) VALUES (:pid, :prod)"), {"pid": promo_id, "prod": pid})
                
                # promotion_stores
                if store_ids and random.random() > 0.5: # 50% are store specific
                    promo_stores = random.sample(store_ids, k=random.randint(1, len(store_ids)))
                    for sid in promo_stores:
                        session.execute(text("INSERT INTO promotion_stores (promotion_id, store_id) VALUES (:pid, :sid)"), {"pid": promo_id, "sid": sid})
                        
                # promotion_discounts
                discount_type = random.choice([1, 2])
                if discount_type == 1: # %
                    discount_val = random.choice([5, 10, 15, 20, 50])
                    max_disc = random.choice([50000, 100000, 200000])
                else: # VND
                    discount_val = random.choice([20000, 50000, 100000])
                    max_disc = discount_val
                    
                session.execute(
                    text("""
                        INSERT INTO promotion_discounts (promotion_id, discount_type, discount_value, max_discount, min_order_value)
                        VALUES (:pid, :type, :val, :max_val, :min_val)
                    """),
                    {
                        "pid": promo_id, "type": discount_type, "val": discount_val, "max_val": max_disc,
                        "min_val": random.choice([0, 100000, 300000, 500000])
                    }
                )
            session.commit()
            print(f" - Inserted {num_promos} promotions.")

if __name__ == "__main__":
    generator = PromotionGenerator()
    generator.run()
