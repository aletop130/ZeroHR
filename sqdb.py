import os
from sqlalchemy import create_engine, Column, String, DateTime, Integer,desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./assunzioni.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit= False)
Base = declarative_base()

class UserSession(Base):
    __tablename__ = "sessions"
    user_id= Column(String, primary_key=True,index=True)
    start_time = Column(DateTime, default=datetime.datetime.now, nullable=True)
    last_access_time = Column(DateTime, default=datetime.datetime.now, nullable=True)
    
class ChatSession(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String, index=True, nullable=True)
    type = Column(String, index=True, nullable=True)
    message = Column(String, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now, nullable=True)
    
def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database initialized.")  

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()