"""
gen_invoice.py — Data Generator cho invoice_db (PostgreSQL)
Phụ thuộc: ecommerce_db, retail_pos_db
"""
import sys
import os
import random
from sqlalchemy import text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import PG_BASE_URL, MSSQL_URL, GEN_CONFIG
from generators.base import BaseGenerator
from sqlalchemy import create_engine


class InvoiceGenerator(BaseGenerator):
    def __init__(self):
        super().__init__(PG_BASE_URL.format(db="postgres") + "?options=-c%20search_path=invoice_db")
        self.pg_engine = create_engine(PG_BASE_URL.format(db="postgres"))
        self.mssql_engine = create_engine(MSSQL_URL)

    def get_sales_data(self):
        ecommerce_orders = []
        pos_orders = []
        # Get Ecommerce Orders
        with self.pg_engine.connect() as conn:
            res_eco = conn.execute(text("SELECT order_number, customer_id, total_amount, order_date FROM ecommerce_db.online_orders WHERE order_status='Delivered'"))
            for r in res_eco.fetchall():
                ecommerce_orders.append({"num": r[0], "cid": r[1], "amt": float(r[2]), "date": r[3], "channel": "ECOMMERCE"})
                
        # Get POS Orders
        with self.mssql_engine.connect() as conn:
            try:
                res_pos = conn.execute(text("SELECT order_number, employee_id, total_amount, order_date FROM sales_orders WHERE status='Completed'"))
                for r in res_pos.fetchall():
                    pos_orders.append({"num": r[0], "cid": None, "amt": float(r[2]), "date": r[3], "channel": "POS"})
            except Exception as e:
                print(f"Warning: Could not fetch from MSSQL: {e}")
            
        return ecommerce_orders, pos_orders

    def run(self):
        print("Generating data for invoice_db...")
        
        self.truncate_table("invoice_taxes")
        self.truncate_table("invoice_items")
        self.truncate_table("invoices")
        
        eco_orders, pos_orders = self.get_sales_data()
        all_orders = eco_orders + pos_orders
        
        if not all_orders:
            print("⚠️ Không có đơn hàng nào để sinh hóa đơn!")
            return
            
        with self.get_session() as session:
            for o in all_orders:
                # Bỏ qua 20% đơn hàng không lấy hóa đơn
                if random.random() < 0.2:
                    continue
                    
                total_amt = o["amt"]
                tax_amt = total_amt * 0.08 # 8% VAT
                subtotal = total_amt - tax_amt
                
                res = session.execute(
                    text("""
                        INSERT INTO invoices (invoice_number, invoice_type, invoice_date, seller_tax_code, buyer_tax_code, buyer_name, currency_code, subtotal, tax_amount, total_amount, xml_file_name, status)
                        VALUES (:num, :type, :date, :stax, :btax, :name, 'VND', :sub, :tax, :total, :xml, 'Issued')
                        RETURNING invoice_id
                    """),
                    {
                        "num": f"INV-{o['date'].strftime('%Y%m%d')}-{self.fake.unique.random_number(digits=5)}",
                        "type": "VAT",
                        "date": o["date"],
                        "stax": "0312345678", # Mã số thuế TCMart
                        "btax": self.fake.numerify(text="03########"),
                        "name": self.fake.company() if random.random() > 0.5 else self.fake.name(),
                        "sub": subtotal,
                        "tax": tax_amt,
                        "total": total_amt,
                        "xml": f"{o['num']}.xml"
                    }
                )
                inv_id = res.scalar()
                
                # Chi tiết
                session.execute(
                    text("""
                        INSERT INTO invoice_items (invoice_id, product_id, tax_rate, description, quantity, unit_price, tax_amount, line_total)
                        VALUES (:iid, NULL, 8, 'Hàng hóa dịch vụ', 1, :sub, :tax, :total)
                    """),
                    {"iid": inv_id, "sub": subtotal, "tax": tax_amt, "total": total_amt}
                )
                
                # Taxes
                session.execute(
                    text("""
                        INSERT INTO invoice_taxes (invoice_id, tax_rate, taxable_amount, tax_amount)
                        VALUES (:iid, 8, :sub, :tax)
                    """),
                    {"iid": inv_id, "sub": subtotal, "tax": tax_amt}
                )
                
            session.commit()
            print(f" - Inserted invoices cho {len(all_orders)} đơn hàng.")

if __name__ == "__main__":
    generator = InvoiceGenerator()
    generator.run()
