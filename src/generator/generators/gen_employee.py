"""
gen_employee.py — Data Generator cho employee_db (Master Data Nhân sự)
"""
import sys
import os
import random
from sqlalchemy import text
from datetime import timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import PG_BASE_URL, GEN_CONFIG
from generators.base import BaseGenerator


class EmployeeGenerator(BaseGenerator):
    def __init__(self):
        super().__init__(PG_BASE_URL.format(db="postgres") + "?options=-c%20search_path=employee_db")

    def run(self):
        print("Generating data for employee_db...")
        
        self.truncate_table("employee_shifts")
        self.truncate_table("employee_assignments")
        self.truncate_table("employees")
        self.truncate_table("positions")
        self.truncate_table("departments")
        
        with self.get_session() as session:
            # 1. Departments
            depts = [
                {"code": "DEP-SALES", "name": "Bán hàng"},
                {"code": "DEP-MKT", "name": "Marketing"},
                {"code": "DEP-HR", "name": "Nhân sự"},
                {"code": "DEP-IT", "name": "Công nghệ thông tin"},
                {"code": "DEP-LOG", "name": "Kho vận Logistics"}
            ]
            dept_ids = []
            for d in depts:
                res = session.execute(
                    text("INSERT INTO departments (department_code, department_name, status) VALUES (:code, :name, 'active') RETURNING department_id"),
                    {"code": d["code"], "name": d["name"]}
                )
                dept_ids.append(res.scalar())
            print(f" - Inserted {len(dept_ids)} departments.")

            # 2. Positions
            positions = [
                {"code": "POS-MGR", "name": "Cửa hàng trưởng / Quản đốc"},
                {"code": "POS-CASHIER", "name": "Thu ngân"},
                {"code": "POS-SALES", "name": "Nhân viên bán hàng"},
                {"code": "POS-WAREHOUSE", "name": "Nhân viên kho"}
            ]
            pos_ids = []
            for p in positions:
                res = session.execute(
                    text("INSERT INTO positions (position_code, position_name, department_id, status) VALUES (:code, :name, :dept, 'active') RETURNING position_id"),
                    {"code": p["code"], "name": p["name"], "dept": random.choice(dept_ids)}
                )
                pos_ids.append(res.scalar())
            print(f" - Inserted {len(pos_ids)} positions.")

            # 3. Employees
            num_employees = GEN_CONFIG.get("num_employees", 50)
            emp_ids = []
            for i in range(1, num_employees + 1):
                res = session.execute(
                    text("""
                        INSERT INTO employees (employee_code, full_name, gender, date_of_birth, phone, email, address, position_id, hire_date, employment_type, status)
                        VALUES (:code, :name, :gender, :dob, :phone, :email, :address, :pos, :hire, :type, :status)
                        RETURNING employee_id
                    """),
                    {
                        "code": f"EMP-{i:04d}",
                        "name": self.fake.name(),
                        "gender": random.choice(["Male", "Female"]),
                        "dob": self.fake.date_of_birth(minimum_age=18, maximum_age=60),
                        "phone": self.vn_phone(),
                        "email": self.fake.email(),
                        "address": self.fake.address(),
                        "pos": random.choice(pos_ids),
                        "hire": self.fake.date_between(start_date='-5y', end_date='today'),
                        "type": random.choice(["FullTime", "PartTime"]),
                        "status": self.status_choices()
                    }
                )
                emp_ids.append(res.scalar())
            print(f" - Inserted {len(emp_ids)} employees.")
            
            # 4. Assignments & Shifts
            for emp_id in emp_ids:
                # Assignment
                session.execute(
                    text("""
                        INSERT INTO employee_assignments (employee_id, assignment_type, store_id, start_date, status)
                        VALUES (:emp, :type, :store, :start, 'active')
                    """),
                    {"emp": emp_id, "type": "Store", "store": random.randint(1, 10), "start": self.fake.date_this_year()}
                )
                
            session.commit()
            print(f" - Inserted assignments.")


if __name__ == "__main__":
    generator = EmployeeGenerator()
    generator.run()
