"""
gen_exchange_rate.py — Data Generator cho exchange_rate_db
"""
import sys
import os
# pyrefly: ignore [missing-import]
import yfinance as yf
import pandas as pd
from datetime import timedelta, date
from sqlalchemy import text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import PG_BASE_URL
from generators.base import BaseGenerator

class ExchangeRateGenerator(BaseGenerator):
    def __init__(self):
        super().__init__(PG_BASE_URL.format(db="postgres") + "?options=-c%20search_path=exchange_rate_db")

    def run(self):
        print("Generating data for exchange_rate_db...")
        
        # 1. Currencies (khoảng 3 records)
        self.truncate_table("exchange_rates")
        self.truncate_table("currencies")

        currencies = [
            {"currency_code": "VND", "currency_name": "Vietnamese Dong", "symbol": "₫"},
            {"currency_code": "USD", "currency_name": "US Dollar", "symbol": "$"},
            {"currency_code": "CNY", "currency_name": "Chinese Yuan", "symbol": "¥"}
        ]
        
        with self.get_session() as session:
            for c in currencies:
                session.execute(
                    text("""
                        INSERT INTO currencies (currency_code, currency_name, symbol) 
                        VALUES (:code, :name, :sym)
                    """),
                    {"code": c["currency_code"], "name": c["currency_name"], "sym": c["symbol"]}
                )
            session.commit()
            print(f" - Inserted {len(currencies)} currencies.")

        # 2. Exchange Rates using Yahoo Finance
        # Fetch 1 year of historical data
        rates = []
        try:
            print(" - Fetching real exchange rates from Yahoo Finance...")
            usd_vnd = yf.download("USDVND=X", period="1y", interval="1d", progress=False)
            cny_vnd = yf.download("CNYVND=X", period="1y", interval="1d", progress=False)
            
            # Format USD
            if not usd_vnd.empty:
                # yfinance returns multi-index columns in newer versions, flatten them
                if isinstance(usd_vnd.columns, pd.MultiIndex):
                    usd_vnd.columns = usd_vnd.columns.get_level_values(0)
                
                for dt, row in usd_vnd.iterrows():
                    rates.append({
                        "from_currency": "USD", "to_currency": "VND", 
                        "rate": float(row['Close']), 
                        "rate_date": dt.date(), 
                        "source": "Yahoo Finance"
                    })
            
            # Format CNY
            if not cny_vnd.empty:
                if isinstance(cny_vnd.columns, pd.MultiIndex):
                    cny_vnd.columns = cny_vnd.columns.get_level_values(0)
                
                for dt, row in cny_vnd.iterrows():
                    rates.append({
                        "from_currency": "CNY", "to_currency": "VND", 
                        "rate": float(row['Close']), 
                        "rate_date": dt.date(), 
                        "source": "Yahoo Finance"
                    })
        except Exception as e:
            print(f" - Warning: Failed to fetch real data ({e}), falling back to mock data.")
            # Fallback
            base_usd_vnd = 25000.0
            base_cny_vnd = 3500.0
            
            start_date = date.today() - timedelta(days=365)
            for i in range(365):
                current_date = start_date + timedelta(days=i)
                usd_rate = base_usd_vnd + self.fake.pyfloat(min_value=-100, max_value=100)
                cny_rate = base_cny_vnd + self.fake.pyfloat(min_value=-50, max_value=50)
                
                rates.append({"from_currency": "USD", "to_currency": "VND", "rate": usd_rate, "rate_date": current_date, "source": "Mock"})
                rates.append({"from_currency": "CNY", "to_currency": "VND", "rate": cny_rate, "rate_date": current_date, "source": "Mock"})

        with self.get_session() as session:
            for r in rates:
                session.execute(
                    text("""
                        INSERT INTO exchange_rates (from_currency, to_currency, rate, rate_date, source) 
                        VALUES (:fc, :tc, :rt, :rd, :src)
                    """),
                    {"fc": r["from_currency"], "tc": r["to_currency"], "rt": r["rate"], "rd": r["rate_date"], "src": r["source"]}
                )
            session.commit()
            print(f" - Inserted {len(rates)} exchange_rates.")

if __name__ == "__main__":
    generator = ExchangeRateGenerator()
    generator.run()
