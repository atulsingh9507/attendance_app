from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
 
Base = declarative_base()
 
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
 