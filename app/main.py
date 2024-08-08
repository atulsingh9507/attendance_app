from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
from typing import Optional
from starlette.middleware.sessions import SessionMiddleware
import logging
 
# Configure logging
logging.basicConfig(level=logging.INFO)
 
# Database setup
DATABASE_URL = "sqlite:///./test.db"
 
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
 
# Database models
class User(Base):
    __tablename__ = "users"
 
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)  # Should be hashed
 
class Attendance(Base):
    __tablename__ = "attendance"
 
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    date = Column(String, index=True)
    punch_in = Column(DateTime, nullable=True)
    punch_out = Column(DateTime, nullable=True)
    status = Column(String, nullable=True)
    punch_in_photo = Column(String, nullable=True)
    punch_out_photo = Column(String, nullable=True)
 
Base.metadata.create_all(bind=engine)
 
app = FastAPI()
 
# Add session middleware
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")
 
# Static files route
app.mount("/static", StaticFiles(directory="static"), name="static")
 
# Dependency to get the DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
 
@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("static/index.html") as f:
        return HTMLResponse(content=f.read())
 
@app.get("/dashboard", response_class=HTMLResponse)
async def read_dashboard(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url='/')
 
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return RedirectResponse(url='/')
 
    user_name = db_user.username
    now = datetime.now()
    attendance = db.query(Attendance).filter(Attendance.user_id == user_id, Attendance.date == now.date()).first()
 
    punch_in_time = attendance.punch_in.isoformat() if attendance and attendance.punch_in else "Not punched in"
    punch_out_time = attendance.punch_out.isoformat() if attendance and attendance.punch_out else "Not punched out"
    work_duration = (attendance.punch_out - attendance.punch_in).total_seconds() / 3600 if attendance and attendance.punch_in and attendance.punch_out else "0 hours"
 
    with open("static/dashboard.html") as f:
        content = f.read()
        content = content.replace("{{username}}", user_name)
        content = content.replace("{{punch_in_time}}", punch_in_time)
        content = content.replace("{{punch_out_time}}", punch_out_time)
        content = content.replace("{{work_duration}}", str(work_duration))
        return HTMLResponse(content=content)
 
@app.post("/signup")
async def signup(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == username).first()
    if db_user:
        return {"message": "User already exists"}
 
    # TODO: Hash the password
    hashed_password = password
    new_user = User(username=username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"id": new_user.id, "username": new_user.username}
 
@app.post("/signin")
async def signin(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == username, User.hashed_password == password).first()
    if db_user:
        response = RedirectResponse(url='/dashboard', status_code=302)
        response.set_cookie(key="user_id", value=str(db_user.id))
        return response
    return {"message": "Invalid username or password"}
 
@app.post("/attendance/punch-in")
async def punch_in(request: Request, db: Session = Depends(get_db)):
    user_id = int(request.cookies.get("user_id", 0))
    now = datetime.now()
    body = await request.json()
    photo = body.get('photo', '')
 
    # Check if user has already punched in today
    attendance = db.query(Attendance).filter(Attendance.user_id == user_id, Attendance.date == now.date().isoformat()).first()
    if attendance and attendance.punch_in:
        return {"message": "Already punched in today"}
 
    if not attendance:
        attendance = Attendance(user_id=user_id, date=now.date().isoformat(), punch_in=now, punch_in_photo=photo)
        db.add(attendance)
    else:
        attendance.punch_in = now
        attendance.punch_in_photo = photo
    db.commit()
    return {"punch_in": now.isoformat(), "photo": photo}
 
@app.post("/attendance/punch-out")
async def punch_out(request: Request, db: Session = Depends(get_db)):
    user_id = int(request.cookies.get("user_id", 0))
    now = datetime.now()
    body = await request.json()
    photo = body.get('photo', '')
 
    # Check if user has already punched out today
    attendance = db.query(Attendance).filter(Attendance.user_id == user_id, Attendance.date == now.date().isoformat()).first()
    if attendance and attendance.punch_out:
        return {"message": "Already punched out today"}
 
    if attendance:
        attendance.punch_out = now
        attendance.punch_out_photo = photo
        # Calculate the status based on time difference
        if attendance.punch_in and attendance.punch_out:
            diff_in_seconds = (attendance.punch_out - attendance.punch_in).total_seconds()
            attendance.status = "Present" if diff_in_seconds >= 8 * 3600 else "Absent"
        db.commit()
    return {"punch_out": now.isoformat(), "punch_in": attendance.punch_in.isoformat() if attendance.punch_in else None, "photo": photo}
 
@app.get("/attendance/monthly")
async def get_monthly_attendance(request: Request, db: Session = Depends(get_db)):
    user_id = int(request.cookies.get("user_id", 0))
    now = datetime.now()
    start_date = datetime(now.year, now.month, 1)
    end_date = datetime(now.year, now.month + 1, 1) if now.month < 12 else datetime(now.year + 1, 1, 1)
    records = db.query(Attendance).filter(Attendance.user_id == user_id, Attendance.date >= str(start_date.date()), Attendance.date < str(end_date.date())).all()
 
    # Get all dates from the current month
    attendance_dict = {}
    for record in records:
        punch_in = record.punch_in.isoformat() if record.punch_in else None
        punch_out = record.punch_out.isoformat() if record.punch_out else None
        status = record.status
        attendance_dict[record.date] = {"punch_in": punch_in, "punch_out": punch_out, "status": status}
   
    # Add default status for dates without records (if needed)
    for i in range(1, (end_date - start_date).days + 1):
        date = (start_date + timedelta(days=i-1)).date()
        if date.isoformat() not in attendance_dict:
            if date <= datetime.now().date():
                attendance_dict[date.isoformat()] = {"punch_in": None, "punch_out": None, "status": "Absent"}
   
    return attendance_dict
 
@app.get("/attendance/all")
async def get_all_users_attendance(db: Session = Depends(get_db)):
    now = datetime.now()
    start_date = datetime(now.year, now.month, 1)
    end_date = datetime(now.year, now.month + 1, 1) if now.month < 12 else datetime(now.year + 1, 1, 1)
 
    # Fetch all attendance records
    records = db.query(Attendance, User).join(User, Attendance.user_id == User.id).filter(
        Attendance.date >= str(start_date.date()), Attendance.date < str(end_date.date())
    ).all()
   
    # Structure the response
    attendance_dict = {}
    for attendance, user in records:
        date = attendance.date
        if user.id not in attendance_dict:
            attendance_dict[user.id] = {
                "username": user.username,
                "attendance": {}
            }
        attendance_dict[user.id]["attendance"][date] = {
            "punch_in": attendance.punch_in.isoformat() if attendance.punch_in else None,
            "punch_out": attendance.punch_out.isoformat() if attendance.punch_out else None,
            "status": attendance.status
        }
   
    # Fill in missing dates
    for user_id, data in attendance_dict.items():
        for i in range(1, (end_date - start_date).days + 1):
            date = (start_date + timedelta(days=i-1)).date()
            if date.isoformat() not in data["attendance"]:
                status = "weekoff" if date.weekday() in (5, 6) else "Absent"
                data["attendance"][date.isoformat()] = {
                    "punch_in": None,
                    "punch_out": None,
                    "status": status
                }
   
    return attendance_dict