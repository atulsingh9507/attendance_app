from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import sqlite3
from datetime import datetime

app = FastAPI()

# Database setup
conn = sqlite3.connect('attendance.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    time_in TEXT,
    time_out TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
''')

conn.commit()

# Models
class User(BaseModel):
    username: str
    password: str

class Attendance(BaseModel):
    user_id: int
    date: str
    time_in: str = None
    time_out: str = None

# Endpoints
@app.post("/signup")
async def signup(user: User):
    try:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (user.username, user.password))
        conn.commit()
        return {"message": "User created successfully"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")

@app.post("/signin")
async def signin(user: User):
    cursor.execute('SELECT id FROM users WHERE username = ? AND password = ?', (user.username, user.password))
    user_record = cursor.fetchone()
    if user_record:
        return {"id": user_record[0], "username": user.username}
    else:
        raise HTTPException(status_code=400, detail="Invalid username or password")

@app.post("/punch_in")
async def punch_in(attendance: Attendance):
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('SELECT * FROM attendance WHERE user_id = ? AND date = ?', (attendance.user_id, today))
    record = cursor.fetchone()
    if record:
        raise HTTPException(status_code=400, detail="Already punched in today")
    else:
        cursor.execute('INSERT INTO attendance (user_id, date, time_in) VALUES (?, ?, ?)', 
                       (attendance.user_id, today, datetime.now().strftime('%H:%M:%S')))
        conn.commit()
        return {"message": "Punch in successful"}

@app.post("/punch_out")
async def punch_out(attendance: Attendance):
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('SELECT * FROM attendance WHERE user_id = ? AND date = ?', (attendance.user_id, today))
    record = cursor.fetchone()
    if record and record[3] is None:
        cursor.execute('UPDATE attendance SET time_out = ? WHERE id = ?', 
                       (datetime.now().strftime('%H:%M:%S'), record[0]))
        conn.commit()
        return {"message": "Punch out successful"}
    else:
        raise HTTPException(status_code=400, detail="Punch in first")

@app.get("/attendance/{user_id}")
async def get_attendance(user_id: int, year: int, month: int):
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-31"
    cursor.execute('''
    SELECT date, time_in, time_out FROM attendance 
    WHERE user_id = ? AND date BETWEEN ? AND ?''', (user_id, start_date, end_date))
    records = cursor.fetchall()
    attendance_list = [{"date": rec[0], "time_in": rec[1], "time_out": rec[2]} for rec in records]
    return attendance_list

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
