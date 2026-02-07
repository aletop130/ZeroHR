import os
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


DATABASE_URL = os.getenv("KEY_FLOW_DATABASE_URL", "sqlite:///./key_flow.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit= False)
Base = declarative_base()


class Workflow(Base):
    __tablename__ = "workflow"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    section = Column(Integer, index=True)   # Numero sezione (1,2,...7)
    status = Column(String, index=True, nullable=True)     # esempi: da_generare, generato, da_giudicare, giudicato
    text = Column(String, nullable=True)                    # Testo generato o da giudicare
    score = Column(Float, nullable=True)                    # Punteggio giudizio (opzionale)
    notes = Column(String, nullable=True) 
    weighted_score = Column(Float, nullable=True)                  # Note miglioramenti (opzionale)
    retry_count = Column(Integer, default=0, nullable=True)       # Numero di retry effettuati

class AllData(Base):
    __tablename__ = "alldata"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    section = Column(Integer, index=True)   # Numero sezione (1,2,...7)
    status = Column(String, index=True, nullable=True)     # esempi: da_generare, generato, da_giudicare, giudicato
    text = Column(String, nullable=True)                    # Testo generato o da giudicare
    score = Column(Float, nullable=True)                    # Punteggio giudizio (opzionale)
    notes = Column(String, nullable=True) 
    weighted_score = Column(Float, nullable=True)                  # Note miglioramenti (opzionale)
    retry_count = Column(Integer, default=0, nullable=True)

def init_db2():
    Base.metadata.create_all(bind=engine)
    print("Database initialized.")  

def get_db2():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()