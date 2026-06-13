from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from loguru import logger
from ..infrastructure.mcp_protocol import McpGateway, McpRequest
from ..application.services import JobApplicationService, CandidateApplicationService, MatchApplicationService
from ..application.commands import (
    CreateJobCommand,
    UpdateJobIntentCommand,
    ApplyJobCommand,
    MatchCandidateCommand,
)
from ..application.dto import JobDTO, CandidateDTO, MatchResultDTO


mcp_router = APIRouter(prefix="/mcp/v1")


@mcp_router.post("/company/jobs")
async def get_company_jobs(
    payload: Dict[str, Any],
    job_service: JobApplicationService = Depends(),
):
    try:
        company_id = payload.get("company_id")
        filters = payload.get("filters", {})
        page = payload.get("page", 1)
        size = payload.get("size", 20)
        
        jobs = await job_service.list_jobs(
            company_id=company_id, 
            status=filters.get("status"),
            page=page, 
            size=size
        )
        
        return {
            "status": "success",
            "data": {
                "jobs": [job.dict() for job in jobs],
                "total": len(jobs),
                "page": page,
                "size": size,
            },
            "message": "获取成功",
        }
    except Exception as e:
        logger.error(f"MCP company jobs error: {str(e)}")
        return {"status": "error", "data": {}, "message": str(e)}


@mcp_router.get("/company/jobs/{job_id}")
async def get_company_job_detail(
    job_id: str,
    job_service: JobApplicationService = Depends(),
):
    try:
        job = await job_service.get_job(job_id=job_id)
        if not job:
            return {"status": "error", "data": {}, "message": "Job not found"}
        
        return {
            "status": "success",
            "data": job.dict(),
            "message": "获取成功",
        }
    except Exception as e:
        logger.error(f"MCP company job detail error: {str(e)}")
        return {"status": "error", "data": {}, "message": str(e)}


@mcp_router.post("/company/search/resume")
async def company_search_resume(
    payload: Dict[str, Any],
    candidate_service: CandidateApplicationService = Depends(),
):
    try:
        criteria = payload.get("criteria", {})
        limit = payload.get("limit", 10)
        
        candidates = await candidate_service.search_candidates(criteria=criteria)
        limited_candidates = candidates[:limit]
        
        return {
            "status": "success",
            "data": {
                "candidates": [c.dict() for c in limited_candidates],
            },
            "message": "搜索成功",
        }
    except Exception as e:
        logger.error(f"MCP company search error: {str(e)}")
        return {"status": "error", "data": {}, "message": str(e)}


@mcp_router.post("/company/recruitment/status")
async def update_recruitment_status(
    payload: Dict[str, Any],
):
    try:
        match_id = payload.get("match_id")
        status = payload.get("status")
        
        return {
            "status": "success",
            "data": {"match_id": match_id, "status": status},
            "message": "状态更新成功",
        }
    except Exception as e:
        logger.error(f"MCP recruitment status error: {str(e)}")
        return {"status": "error", "data": {}, "message": str(e)}


@mcp_router.get("/candidate/profile")
async def get_candidate_profile(
    payload: Dict[str, Any],
    candidate_service: CandidateApplicationService = Depends(),
):
    try:
        candidate_id = payload.get("candidate_id")
        candidate = await candidate_service.get_candidate(candidate_id=candidate_id)
        
        if not candidate:
            return {"status": "error", "data": {}, "message": "Candidate not found"}
        
        return {
            "status": "success",
            "data": candidate.dict(),
            "message": "获取成功",
        }
    except Exception as e:
        logger.error(f"MCP candidate profile error: {str(e)}")
        return {"status": "error", "data": {}, "message": str(e)}


@mcp_router.post("/candidate/job_intent")
async def update_candidate_job_intent(
    payload: Dict[str, Any],
    candidate_service: CandidateApplicationService = Depends(),
):
    try:
        candidate_id = payload.get("candidate_id")
        job_intent = payload.get("job_intent", {})
        
        updated = await candidate_service.update_job_intent(
            candidate_id=candidate_id,
            job_intent=job_intent,
        )
        
        return {
            "status": "success",
            "data": updated.dict(),
            "message": "更新成功",
        }
    except Exception as e:
        logger.error(f"MCP job intent error: {str(e)}")
        return {"status": "error", "data": {}, "message": str(e)}


@mcp_router.post("/candidate/apply")
async def candidate_apply_job(
    payload: Dict[str, Any],
    match_service: MatchApplicationService = Depends(),
):
    try:
        candidate_id = payload.get("candidate_id")
        job_id = payload.get("job_id")
        
        matches = await match_service.match_candidate_with_jobs(
            candidate_id=candidate_id,
            top_n=1,
        )
        
        return {
            "status": "success",
            "data": {
                "candidate_id": candidate_id,
                "job_id": job_id,
                "applied": True,
            },
            "message": "申请成功",
        }
    except Exception as e:
        logger.error(f"MCP apply error: {str(e)}")
        return {"status": "error", "data": {}, "message": str(e)}


@mcp_router.get("/candidate/status")
async def get_candidate_application_status(
    payload: Dict[str, Any],
    match_service: MatchApplicationService = Depends(),
):
    try:
        candidate_id = payload.get("candidate_id")
        
        matches = await match_service.list_matches_by_candidate(candidate_id=candidate_id)
        
        return {
            "status": "success",
            "data": {
                "applications": [m.dict() for m in matches],
                "count": len(matches),
            },
            "message": "获取成功",
        }
    except Exception as e:
        logger.error(f"MCP status error: {str(e)}")
        return {"status": "error", "data": {}, "message": str(e)}


@mcp_router.post("/match")
async def trigger_match(
    payload: Dict[str, Any],
    match_service: MatchApplicationService = Depends(),
):
    try:
        candidate_id = payload.get("candidate_id")
        top_n = payload.get("top_n", 10)
        
        matches = await match_service.match_candidate_with_jobs(
            candidate_id=candidate_id,
            top_n=top_n,
        )
        
        return {
            "status": "success",
            "data": {
                "matches": [m.match.dict() for m in matches],
                "job_details": [m.job.dict() for m in matches],
            },
            "message": "匹配成功",
        }
    except Exception as e:
        logger.error(f"MCP match error: {str(e)}")
        return {"status": "error", "data": {}, "message": str(e)}
