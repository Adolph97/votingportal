from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from .database import Base

class Candidate(Base):
    __tablename__ = "candidates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    club = Column(String(100))
    image_path = Column(String(200))
    votes = Column(Integer, default=0)

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String(100), unique=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    vote_count = Column(Integer)
    amount = Column(Float)
    email = Column(String(100))
    status = Column(String(20))  # pending, success, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())