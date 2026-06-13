from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class CreateCompanyCommand(BaseModel):
    name: str
    mcp_server_url: str
    api_key: str


class UpdateCompanyCommand(BaseModel):
    company_id: str
    name: Optional[str] = None
    mcp_server_url: Optional[str] = None
    api_key: Optional[str] = None
    status: Optional[str] = None


class DeleteCompanyCommand(BaseModel):
    company_id: str


class CreateJobCommand(BaseModel):
    company_id: str
    title: str
    description: Optional[str] = ""
    requirements: Optional[str] = ""
    location: Optional[str] = ""
    salary_range: Optional[str] = ""
    tags: Optional[List[str]] = []


class UpdateJobCommand(BaseModel):
    job_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None


class CreateCandidateCommand(BaseModel):
    mcp_server_url: str
    api_key: str
    name: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[str] = ""
    resume_text: Optional[str] = ""
    skills: Optional[List[str]] = []
    experience: Optional[str] = ""
    education: Optional[str] = ""
    job_intent: Optional[Dict[str, Any]] = {}


class UpdateCandidateCommand(BaseModel):
    candidate_id: str
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    resume_text: Optional[str] = None
    skills: Optional[List[str]] = None
    experience: Optional[str] = None
    education: Optional[str] = None
    job_intent: Optional[Dict[str, Any]] = None


class MatchJobCommand(BaseModel):
    job_id: str
    top_n: Optional[int] = 10


class MatchCandidateCommand(BaseModel):
    candidate_id: str
    top_n: Optional[int] = 10


class UpdateMatchStatusCommand(BaseModel):
    match_id: str
    status: str


class ProcessTransitionCommand(BaseModel):
    match_id: str
    new_state: str
    comment: Optional[str] = ""


class SearchResumeCommand(BaseModel):
    company_id: str
    criteria: Dict[str, Any]
    limit: Optional[int] = 10


class UpdateJobIntentCommand(BaseModel):
    candidate_id: str
    job_intent: Dict[str, Any]


class ApplyJobCommand(BaseModel):
    candidate_id: str
    job_id: str
