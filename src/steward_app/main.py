import os
import json
import datetime
# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Request, Form, Depends
# pyrefly: ignore [missing-import]
from fastapi.templating import Jinja2Templates
# pyrefly: ignore [missing-import]
from fastapi.responses import HTMLResponse, RedirectResponse
# pyrefly: ignore [missing-import]
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base, SuspectRecord

# ─── Database Setup ────────────────────────────────────────────────────────
DB_DIR = "/app/data" if os.path.exists("/app/data") else "."
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_DIR}/steward.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ─── FastAPI App ────────────────────────────────────────────────────────────
app = FastAPI(title="TC Mart - Data Steward App")

# Templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Trang chủ hiển thị danh sách các bản ghi nghi ngờ (PENDING)."""
    records = db.query(SuspectRecord).filter(SuspectRecord.status == "PENDING").order_by(SuspectRecord.created_at.desc()).all()
    
    # Parse JSON cho dễ hiển thị trên giao diện
    parsed_records = []
    for r in records:
        try:
            payload = json.loads(r.raw_payload_json)
        except:
            payload = {"error": "Invalid JSON"}
        parsed_records.append({
            "id": r.id,
            "table": r.table_name,
            "rule": r.violation_rule,
            "message": r.error_message,
            "payload": payload,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })

    return templates.TemplateResponse("index.html", {"request": request, "records": parsed_records})


@app.post("/action/{record_id}")
async def handle_action(record_id: int, action: str = Form(...), updated_json: str = Form(None), db: Session = Depends(get_db)):
    """Xử lý Duyệt (APPROVE) hoặc Hủy (REJECT) một bản ghi."""
    record = db.query(SuspectRecord).filter(SuspectRecord.id == record_id).first()
    if not record:
        return RedirectResponse(url="/", status_code=303)
        
    if action == "APPROVE":
        record.status = "APPROVED"
        if updated_json:
            # Lưu lại chuỗi JSON đã được Data Steward sửa đổi
            record.raw_payload_json = updated_json
    elif action == "REJECT":
        record.status = "REJECTED"
        
    record.resolved_at = datetime.datetime.utcnow()
    db.commit()
    
    return RedirectResponse(url="/", status_code=303)


# (Optional) Endpoint API để Airflow hoặc PySpark đẩy dữ liệu lỗi vào SQLite
@app.post("/api/suspects")
async def ingest_suspect(payload: dict, db: Session = Depends(get_db)):
    new_record = SuspectRecord(
        table_name=payload.get("table_name", "unknown"),
        violation_rule=payload.get("violation_rule", "UNKNOWN_RULE"),
        error_message=payload.get("error_message", ""),
        raw_payload_json=json.dumps(payload.get("raw_payload_json", {})),
        status="PENDING"
    )
    db.add(new_record)
    db.commit()
    return {"status": "success", "id": new_record.id}
