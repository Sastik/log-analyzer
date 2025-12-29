from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.config import settings

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class LogEntryDB(Base):
    __tablename__ = "log_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    correlation_id = Column(String(100), index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    api_name = Column(String(100), index=True)
    service_name = Column(String(200), index=True)
    thread = Column(String(100))
    logger = Column(String(200))
    session_id = Column(String(100), index=True)
    log_type = Column(String(20))
    party_id = Column(String(100))
    request_data = Column(JSON)
    response_data = Column(JSON)
    has_error = Column(String(10), index=True)
    error_message = Column(Text)
    error_trace = Column(Text)
    duration_ms = Column(Integer)
    url = Column(Text)
    log_time = Column(String(100))
    header_log = Column(JSON)
    file_name = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

# Create tables
def init_db():
    Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()