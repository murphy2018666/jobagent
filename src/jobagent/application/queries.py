from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class GetCompanyQuery(BaseModel):
    company_id: str


class ListCompaniesQuery(BaseModel):
    status: Optional[str] = None
    page: int = 1
    size: int = 20


class GetJobQuery(BaseModel):
    job_id: str


class ListJobsQuery(BaseModel):
    company_id: Optional[str] = None
    status: Optional[str] = None
    page: int = 1
    size: int = 20


class SearchJobsQuery(BaseModel):
    filters: Dict[str, Any]
    page: int = 1
    size: int = 20


class GetCandidateQuery(BaseModel):
    candidate_id: str


class SearchCandidatesQuery(BaseModel):
    criteria: Dict[str, Any]
    page: int = 1
    size: int = 20


class GetMatchQuery(BaseModel):
    match_id: str


class ListMatchesByJobQuery(BaseModel):
    job_id: str
    status: Optional[str] = None


class ListMatchesByCandidateQuery(BaseModel):
    candidate_id: str
    status: Optional[str] = None


class GetProcessQuery(BaseModel):
    match_id: str


class GetProcessHistoryQuery(BaseModel):
    match_id: str


class SearchResumeQuery(BaseModel):
    company_id: str
    criteria: Dict[str, Any]
    limit: int = 10
