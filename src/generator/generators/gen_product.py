"""
gen_product.py — Data Generator cho product_db (Master Data)
"""
import sys
import os
import random
from sqlalchemy import text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import PG_BASE_URL, GEN_CONFIG
from generators.base import BaseGenerator


class ProductGenerator(BaseGenerator):
    def __init__(self):
        super().__init__(PG_BASE_URL.format(db="postgres") + "?options=-c%20search_path=product_db")

    def run(self):
        print("Generating data for product_db...")
        
        self.truncate_table("product_prices")
        self.truncate_table("products")
        self.truncate_table("brands")
        self.truncate_table("categories")
        
        with self.get_session() as session:
            # 1. Categories
            categories_data = [
                {"code": "CAT-BEV", "name": "Đồ uống"},
                {"code": "CAT-SNK", "name": "Bánh kẹo & Ăn vặt"},
                {"code": "CAT-FRE", "name": "Thực phẩm tươi sống"},
                {"code": "CAT-COS", "name": "Mỹ phẩm & Chăm sóc cá nhân"}
            ]
            category_ids = []
            for c in categories_data:
                res = session.execute(
                    text("INSERT INTO categories (category_code, category_name) VALUES (:code, :name) RETURNING category_id"),
                    {"code": c["code"], "name": c["name"]}
                )
                category_ids.append(res.scalar())
            print(f" - Inserted {len(category_ids)} categories.")

            # 2. Brands
            brands_data = [
                {"code": "BRD-VNM", "name": "Vinamilk"},
                {"code": "BRD-PEP", "name": "PepsiCo"},
                {"code": "BRD-MAS", "name": "Masan Consumer"},
                {"code": "BRD-ULV", "name": "Unilever"},
                {"code": "BRD-HND", "name": "Heineken"}
            ]
            brand_ids = []
            for b in brands_data:
                res = session.execute(
                    text("INSERT INTO brands (brand_code, brand_name) VALUES (:code, :name) RETURNING brand_id"),
                    {"code": b["code"], "name": b["name"]}
                )
                brand_ids.append(res.scalar())
            print(f" - Inserted {len(brand_ids)} brands.")

            # 3. Products
            num_products = GEN_CONFIG.get("num_products", 200)
            product_ids = []
            for i in range(1, num_products + 1):
                cat_id = random.choice(category_ids)
                brand_id = random.choice(brand_ids)
                cost_price = round(random.uniform(5000, 500000), -3) # Làm tròn đến nghìn đồng
                
                res = session.execute(
                    text("""
                        INSERT INTO products (product_code, product_name, category_id, brand_id, employee_id, unit, barcode, product_type, cost_price, status)
                        VALUES (:code, :name, :cat, :brd, :emp, :unit, :bc, :type, :cost, :status)
                        RETURNING product_id
                    """),
                    {
                        "code": f"PROD-{i:05d}",
                        "name": f"{self.fake.word().capitalize()} Product {i}",
                        "cat": cat_id,
                        "brd": brand_id,
                        "emp": random.randint(1, 50), # Giả lập người tạo
                        "unit": random.choice(["Chai", "Hộp", "Gói", "Thùng", "Lốc"]),
                        "bc": self.fake.ean(length=13),
                        "type": random.choice(["Finished_Good", "Raw_Material"]),
                        "cost": cost_price,
                        "status": self.status_choices()
                    }
                )
                product_ids.append((res.scalar(), cost_price))
            print(f" - Inserted {len(product_ids)} products.")

            # 4. Product Prices (Tạo giá bán = giá vốn + 30%)
            for pid, cost in product_ids:
                retail_price = cost * 1.3
                wholesale_price = cost * 1.15
                
                session.execute(
                    text("""
                        INSERT INTO product_prices (product_id, price_type, price, currency_code)
                        VALUES 
                        (:pid, 'Retail', :rp, 'VND'),
                        (:pid, 'Wholesale', :wp, 'VND')
                    """),
                    {"pid": pid, "rp": retail_price, "wp": wholesale_price}
                )
            session.commit()
            print(f" - Inserted {len(product_ids) * 2} product prices.")

if __name__ == "__main__":
    generator = ProductGenerator()
    generator.run()
