from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Tasks(Base):
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True, index=True)
    celery_task_id = Column(String(255), unique=True, nullable=True, index=True)
    status = Column(String(50), default='PENDING')
    patient_id = Column(Integer, nullable=False, index=True)
    
    # Progress
    current_lines = Column(Integer, default=0)
    last_output = Column(Text)
    
    # Directory
    workdir = Column(String(500))
    outdir = Column(String(500))
    
    # Results
    return_code = Column(Integer)
    stdout = Column(Text)
    stderr = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)