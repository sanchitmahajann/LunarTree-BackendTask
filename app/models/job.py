from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class JobBase(BaseModel):
    job_id: str
    original_filename: str
    status: str
    timestamp: datetime

class JobCreate(JobBase):
    pass

class JobUpdate(BaseModel):
    extracted_company_username: Optional[str] = None
    github_members: Optional[List[str]] = None
    status: str

class Job(JobBase):
    extracted_company_username: Optional[str] = None
    github_members: Optional[List[str]] = None

    class Config:
        from_attributes = True 