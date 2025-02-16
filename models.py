from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import Optional

Base = declarative_base()

class AWSCredentials(BaseModel):
    aws_access_key_id: str = Field(..., description="AWS Access Key ID")
    aws_secret_access_key: str = Field(..., description="AWS Secret Access Key")
    region_name: str = Field(..., description="AWS Region Name")

class IPAllocationHistory(Base):
    __tablename__ = 'ip_allocation_history'
    
    id = Column(Integer, primary_key=True)
    ip_address = Column(String, nullable=False)
    allocation_id = Column(String, nullable=False)
    allocated_at = Column(DateTime, default=datetime.utcnow)
    released_at = Column(DateTime, nullable=True)
    region = Column(String, nullable=False)
