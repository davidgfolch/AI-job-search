from typing import Optional, List, Union
from datetime import datetime
from pydantic import BaseModel

class JobBase(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    url: Optional[str] = None
    markdown: Optional[str] = None
    easy_apply: Optional[bool] = None
    web_page: Optional[str] = None
    salary: Optional[str] = None
    required_technologies: Optional[str] = None
    optional_technologies: Optional[str] = None
    client: Optional[str] = None
    comments: Optional[str] = None
    ai_enrich_error: Optional[str] = None
    cv_match_percentage: Optional[float] = None
    
    # Boolean fields
    flagged: Optional[bool] = None
    like: Optional[bool] = None
    ignored: Optional[bool] = None
    seen: Optional[bool] = None
    applied: Optional[bool] = None
    discarded: Optional[bool] = None
    closed: Optional[bool] = None
    interview_rh: Optional[bool] = None
    interview: Optional[bool] = None
    interview_tech: Optional[bool] = None
    interview_technical_test: Optional[bool] = None
    interview_technical_test_done: Optional[bool] = None
    ai_enriched: Optional[bool] = None

class Job(JobBase):
    id: int
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    merged: Optional[datetime] = None
    merged_id: Optional[Union[str, int]] = None

class JobCreate(JobBase):
    title: str
    company: str
    location: Optional[str] = None
    url: Optional[str] = None
    markdown: Optional[str] = None
    web_page: Optional[str] = None

class JobUpdate(JobBase):
    pass

class JobListResponse(BaseModel):
    items: List[Job]
    total: int
    page: int
    size: int

class AppliedCompanyJob(BaseModel):
    id: int
    created: Optional[str] = None

class WatcherStatsResponse(BaseModel):
    total: int
    new_items: int
