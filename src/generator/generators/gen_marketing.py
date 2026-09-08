import sys
import os
import random
from sqlalchemy import text
from datetime import timedelta, date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import PG_BASE_URL, GEN_CONFIG
from generators.base import BaseGenerator
from sqlalchemy import create_engine

class MarketingGenerator(BaseGenerator):
    def __init__(self):
        super().__init__(PG_BASE_URL.format(db="postgres") + "?options=-c%20search_path=marketing_db")
        self.pg_engine = create_engine(PG_BASE_URL.format(db="postgres"))

    def get_master_data(self):
        employee_ids = []
        with self.pg_engine.connect() as conn:
            res_emp = conn.execute(text("SELECT employee_id FROM employee_db.employees WHERE status='active'"))
            employee_ids = [r[0] for r in res_emp.fetchall()]
        return employee_ids

    def run(self):
        print("Generating data for marketing_db...")
        employee_ids = self.get_master_data()
        if not employee_ids:
            print("❌ Lỗi: Cần chạy gen_employee.py trước!")
            return

        self.truncate_table("campaign_costs")
        self.truncate_table("clicks")
        self.truncate_table("impressions")
        self.truncate_table("campaign_channels")
        self.truncate_table("campaigns")
        
        with self.get_session() as session:
            api_data = []
            num_campaigns = GEN_CONFIG.get("num_campaigns", 30)
            for i in range(1, num_campaigns + 1):
                start_date = self.fake.date_time_this_year()
                end_date = start_date + timedelta(days=random.randint(10, 60))
                
                res = session.execute(
                    text("""
                        INSERT INTO campaigns (campaign_code, campaign_name, employee_id, start_date, end_date, budget, status)
                        VALUES (:code, :name, :emp, :start, :end, :budget, :status)
                        RETURNING campaign_id
                    """),
                    {
                        "code": f"MKT-{i:03d}-{start_date.strftime('%m%y')}",
                        "name": f"Campaign {self.fake.catch_phrase()}",
                        "emp": random.choice(employee_ids),
                        "start": start_date,
                        "end": end_date,
                        "budget": random.randint(10, 500) * 1000000, # 10m to 500m
                        "status": random.choice(["Active", "Completed", "Planned"])
                    }
                )
                camp_id = res.scalar()
                
                # channels
                channels = ["Facebook Ads", "Google Search", "Tiktok", "Email", "Affiliate"]
                camp_channels = random.sample(channels, k=random.randint(1, 4))
                channel_map = {}
                for ch in camp_channels:
                    res_ch = session.execute(
                        text("INSERT INTO campaign_channels (campaign_id, channel_name) VALUES (:cid, :name) RETURNING channel_id"),
                        {"cid": camp_id, "name": ch}
                    )
                    channel_map[ch] = res_ch.scalar()
                
                # impressions & clicks & costs
                # generate per day
                current_date = start_date.date()
                end_d = min(end_date.date(), date.today())
                
                while current_date <= end_d:
                    for ch, chan_id in channel_map.items():
                        # random stats
                        impr = random.randint(1000, 50000)
                        click = int(impr * random.uniform(0.01, 0.1)) # 1-10% CTR
                        cost = click * random.randint(1000, 10000) # CPC 1k-10k
                        
                        api_data.append({
                            "campaign_id": camp_id,
                            "channel_id": chan_id,
                            "channel_name": ch,
                            "date": current_date.strftime('%Y-%m-%d'),
                            "impressions": impr,
                            "clicks": click,
                            "spend": cost,
                            "currency": "VND"
                        })
                        
                    current_date += timedelta(days=1)
                
            session.commit()
            print(f" - Inserted {num_campaigns} marketing campaigns.")

            # Xuất JSON
            import json
            output_dir = os.path.join(os.path.dirname(__file__), "../../../data/raw/marketing_ads")
            os.makedirs(output_dir, exist_ok=True)
            
            output_file = os.path.join(output_dir, f"social_ads_metrics_{date.today().strftime('%Y%m%d')}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({"status": "success", "data": api_data}, f, ensure_ascii=False, indent=2)
                
            print(f" - Exported {len(api_data)} daily metrics to JSON: {output_file}")

if __name__ == "__main__":
    generator = MarketingGenerator()
    generator.run()
