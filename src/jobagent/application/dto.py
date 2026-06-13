from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class CompanyDTO(BaseModel):
    id: Optional[str] = None
    name: str
    mcp_server_url: str
    api_key: str
    status: str = "active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobDTO(BaseModel):
    id: Optional[str] = None
    company_id: str
    title: str
    description: str = ""
    requirements: str = ""
    location: str = ""
    salary_range: str = ""
    tags: List[str] = []
    status: str = "open"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CandidateDTO(BaseModel):
    id: Optional[str] = None
    mcp_server_url: str
    api_key: str
    name: str = ""
    phone: str = ""
    email: str = ""
    resume_text: str = ""
    skills: List[str] = []
    experience: str = ""
    education: str = ""
    job_intent: Dict[str, Any] = {}
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MatchDTO(BaseModel):
    id: Optional[str] = None
    job_id: str
    candidate_id: str
    score: float
    match_reasons: List[str] = []
    status: str = "pending"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProcessDTO(BaseModel):
    id: Optional[str] = None
    match_id: str
    current_state: str
    history: List[Dict[str, Any]] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MatchResultDTO(BaseModel):
    match: MatchDTO
    job: JobDTO
    candidate: CandidateDTO


class PaginatedResultDTO(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int


class ErrorResponseDTO(BaseModel):
    code: int
    message: str
    detail: Optional[str] = None
