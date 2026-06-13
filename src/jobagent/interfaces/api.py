from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from typing import List, Optional, Dict, Any
from loguru import logger
from ..application.services import (
    CompanyApplicationService,
    JobApplicationService,
    CandidateApplicationService,
    MatchApplicationService,
    ProcessApplicationService,
    SearchApplicationService,
)
from ..application.commands import (
    CreateCompanyCommand,
    UpdateCompanyCommand,
    DeleteCompanyCommand,
    CreateJobCommand,
    UpdateJobCommand,
    CreateCandidateCommand,
    UpdateCandidateCommand,
    MatchJobCommand,
    MatchCandidateCommand,
    UpdateMatchStatusCommand,
    ProcessTransitionCommand,
    SearchResumeCommand,
    UpdateJobIntentCommand,
    ApplyJobCommand,
)
from ..application.queries import (
    GetCompanyQuery,
    ListCompaniesQuery,
    GetJobQuery,
    ListJobsQuery,
    GetCandidateQuery,
    SearchCandidatesQuery,
    GetMatchQuery,
    ListMatchesByJobQuery,
    ListMatchesByCandidateQuery,
    GetProcessQuery,
)
from ..application.dto import CompanyDTO, JobDTO, CandidateDTO, MatchDTO, ProcessDTO, MatchResultDTO, ErrorResponseDTO


router = APIRouter()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# 企业管理接口
@router.post("/companies", response_model=CompanyDTO, status_code=status.HTTP_201_CREATED)
async def create_company(
    command: CreateCompanyCommand,
    service: CompanyApplicationService = Depends(),
):
    """
    创建企业
    
    创建一个新的企业实体，包含企业基本信息和MCP服务器配置。
    
    Args:
        command: 创建企业命令，包含企业名称、MCP服务器URL、API密钥等信息
        service: 企业应用服务实例
        
    Returns:
        CompanyDTO: 创建的企业信息
        
    Raises:
        HTTPException: 创建失败时返回400状态码
    """
    try:
        return await service.create_company(command)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/companies/{company_id}", response_model=CompanyDTO)
async def get_company(
    company_id: str,
    service: CompanyApplicationService = Depends(),
):
    """
    获取企业详情
    
    根据企业ID获取企业详细信息。
    
    Args:
        company_id: 企业ID
        service: 企业应用服务实例
        
    Returns:
        CompanyDTO: 企业详细信息
        
    Raises:
        HTTPException: 企业不存在时返回404状态码
    """
    company = await service.get_company(GetCompanyQuery(company_id=company_id))
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.get("/companies", response_model=List[CompanyDTO])
async def list_companies(
    status: Optional[str] = None,
    page: int = 1,
    size: int = 20,
    service: CompanyApplicationService = Depends(),
):
    """
    列出企业列表
    
    获取企业列表，支持状态过滤和分页。
    
    Args:
        status: 状态过滤（可选）
        page: 页码，默认为1
        size: 每页数量，默认为20
        service: 企业应用服务实例
        
    Returns:
        List[CompanyDTO]: 企业列表
    """
    return await service.list_companies(ListCompaniesQuery(status=status, page=page, size=size))


@router.put("/companies/{company_id}", response_model=CompanyDTO)
async def update_company(
    company_id: str,
    command: UpdateCompanyCommand,
    service: CompanyApplicationService = Depends(),
):
    """
    更新企业信息
    
    更新指定企业的基本信息。
    
    Args:
        company_id: 企业ID
        command: 更新企业命令
        service: 企业应用服务实例
        
    Returns:
        CompanyDTO: 更新后的企业信息
        
    Raises:
        HTTPException: 更新失败时返回400状态码
    """
    command.company_id = company_id
    try:
        return await service.update_company(command)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/companies/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: str,
    service: CompanyApplicationService = Depends(),
):
    """
    删除企业
    
    删除指定的企业实体。
    
    Args:
        company_id: 企业ID
        service: 企业应用服务实例
        
    Raises:
        HTTPException: 企业不存在时返回404状态码
    """
    success = await service.delete_company(DeleteCompanyCommand(company_id=company_id))
    if not success:
        raise HTTPException(status_code=404, detail="Company not found")


# 岗位管理接口
@router.post("/jobs", response_model=JobDTO, status_code=status.HTTP_201_CREATED)
async def create_job(
    command: CreateJobCommand,
    service: JobApplicationService = Depends(),
):
    """
    创建岗位
    
    创建一个新的招聘岗位。
    
    Args:
        command: 创建岗位命令，包含岗位标题、描述、要求等信息
        service: 岗位应用服务实例
        
    Returns:
        JobDTO: 创建的岗位信息
        
    Raises:
        HTTPException: 创建失败时返回400状态码
    """
    try:
        return await service.create_job(command)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/jobs/{job_id}", response_model=JobDTO)
async def get_job(
    job_id: str,
    service: JobApplicationService = Depends(),
):
    """
    获取岗位详情
    
    根据岗位ID获取岗位详细信息。
    
    Args:
        job_id: 岗位ID
        service: 岗位应用服务实例
        
    Returns:
        JobDTO: 岗位详细信息
        
    Raises:
        HTTPException: 岗位不存在时返回404状态码
    """
    job = await service.get_job(GetJobQuery(job_id=job_id))
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/jobs", response_model=List[JobDTO])
async def list_jobs(
    company_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    size: int = 20,
    service: JobApplicationService = Depends(),
):
    """
    列出岗位列表
    
    获取岗位列表，支持按企业ID和状态过滤，支持分页。
    
    Args:
        company_id: 企业ID过滤（可选）
        status: 状态过滤（可选）
        page: 页码，默认为1
        size: 每页数量，默认为20
        service: 岗位应用服务实例
        
    Returns:
        List[JobDTO]: 岗位列表
    """
    return await service.list_jobs(ListJobsQuery(company_id=company_id, status=status, page=page, size=size))


@router.put("/jobs/{job_id}", response_model=JobDTO)
async def update_job(
    job_id: str,
    command: UpdateJobCommand,
    service: JobApplicationService = Depends(),
):
    """
    更新岗位信息
    
    更新指定岗位的基本信息。
    
    Args:
        job_id: 岗位ID
        command: 更新岗位命令
        service: 岗位应用服务实例
        
    Returns:
        JobDTO: 更新后的岗位信息
        
    Raises:
        HTTPException: 更新失败时返回400状态码
    """
    command.job_id = job_id
    try:
        return await service.update_job(command)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/jobs/{job_id}/sync", response_model=List[JobDTO])
async def sync_jobs(
    job_id: str,
    service: JobApplicationService = Depends(),
):
    """
    同步岗位数据
    
    从企业MCP服务器同步岗位数据。
    
    Args:
        job_id: 岗位ID（实际为企业ID，此处参数名有误，应为company_id）
        service: 岗位应用服务实例
        
    Returns:
        List[JobDTO]: 同步的岗位列表
        
    Raises:
        HTTPException: 同步失败时返回400状态码
    """
    try:
        return await service.sync_jobs_from_mcp(job_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# 候选人管理接口
@router.post("/candidates", response_model=CandidateDTO, status_code=status.HTTP_201_CREATED)
async def create_candidate(
    command: CreateCandidateCommand,
    service: CandidateApplicationService = Depends(),
):
    """
    创建候选人
    
    创建一个新的候选人实体。
    
    Args:
        command: 创建候选人命令，包含候选人基本信息
        service: 候选人应用服务实例
        
    Returns:
        CandidateDTO: 创建的候选人信息
        
    Raises:
        HTTPException: 创建失败时返回400状态码
    """
    try:
        return await service.create_candidate(command)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/candidates/{candidate_id}", response_model=CandidateDTO)
async def get_candidate(
    candidate_id: str,
    service: CandidateApplicationService = Depends(),
):
    """
    获取候选人详情
    
    根据候选人ID获取候选人详细信息。
    
    Args:
        candidate_id: 候选人ID
        service: 候选人应用服务实例
        
    Returns:
        CandidateDTO: 候选人详细信息
        
    Raises:
        HTTPException: 候选人不存在时返回404状态码
    """
    candidate = await service.get_candidate(GetCandidateQuery(candidate_id=candidate_id))
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@router.put("/candidates/{candidate_id}", response_model=CandidateDTO)
async def update_candidate(
    candidate_id: str,
    command: UpdateCandidateCommand,
    service: CandidateApplicationService = Depends(),
):
    """
    更新候选人信息
    
    更新指定候选人的基本信息。
    
    Args:
        candidate_id: 候选人ID
        command: 更新候选人命令
        service: 候选人应用服务实例
        
    Returns:
        CandidateDTO: 更新后的候选人信息
        
    Raises:
        HTTPException: 更新失败时返回400状态码
    """
    command.candidate_id = candidate_id
    try:
        return await service.update_candidate(command)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/candidates/{candidate_id}/job_intent", response_model=CandidateDTO)
async def update_job_intent(
    candidate_id: str,
    job_intent: Dict[str, Any],
    service: CandidateApplicationService = Depends(),
):
    """
    更新候选人求职意向
    
    更新候选人的求职意向信息，如期望职位、工作地点等。
    
    Args:
        candidate_id: 候选人ID
        job_intent: 求职意向信息
        service: 候选人应用服务实例
        
    Returns:
        CandidateDTO: 更新后的候选人信息
        
    Raises:
        HTTPException: 更新失败时返回400状态码
    """
    command = UpdateJobIntentCommand(candidate_id=candidate_id, job_intent=job_intent)
    try:
        return await service.update_job_intent(command)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# 匹配管理接口
@router.post("/match/job/{job_id}", response_model=List[MatchResultDTO])
async def match_job(
    job_id: str,
    top_n: int = 10,
    service: MatchApplicationService = Depends(),
):
    """
    岗位匹配候选人
    
    根据岗位ID查找最匹配的候选人。
    
    Args:
        job_id: 岗位ID
        top_n: 返回前N个匹配结果，默认为10
        service: 匹配应用服务实例
        
    Returns:
        List[MatchResultDTO]: 匹配结果列表
        
    Raises:
        HTTPException: 匹配失败时返回400状态码
    """
    command = MatchJobCommand(job_id=job_id, top_n=top_n)
    try:
        return await service.match_job_with_candidates(command)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/match/candidate/{candidate_id}", response_model=List[MatchResultDTO])
async def match_candidate(
    candidate_id: str,
    top_n: int = 10,
    service: MatchApplicationService = Depends(),
):
    """
    候选人匹配岗位
    
    根据候选人ID查找最匹配的岗位。
    
    Args:
        candidate_id: 候选人ID
        top_n: 返回前N个匹配结果，默认为10
        service: 匹配应用服务实例
        
    Returns:
        List[MatchResultDTO]: 匹配结果列表
        
    Raises:
        HTTPException: 匹配失败时返回400状态码
    """
    command = MatchCandidateCommand(candidate_id=candidate_id, top_n=top_n)
    try:
        return await service.match_candidate_with_jobs(command)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/match/{match_id}", response_model=MatchDTO)
async def get_match(
    match_id: str,
    service: MatchApplicationService = Depends(),
):
    """
    获取匹配详情
    
    根据匹配ID获取匹配详细信息。
    
    Args:
        match_id: 匹配记录ID
        service: 匹配应用服务实例
        
    Returns:
        MatchDTO: 匹配详细信息
        
    Raises:
        HTTPException: 匹配记录不存在时返回404状态码
    """
    match = await service.get_match(GetMatchQuery(match_id=match_id))
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match


@router.put("/match/{match_id}/status", response_model=MatchDTO)
async def update_match_status(
    match_id: str,
    status: str,
    service: MatchApplicationService = Depends(),
):
    """
    更新匹配状态
    
    更新匹配记录的状态。
    
    Args:
        match_id: 匹配记录ID
        status: 新状态
        service: 匹配应用服务实例
        
    Returns:
        MatchDTO: 更新后的匹配信息
        
    Raises:
        HTTPException: 更新失败时返回400状态码
    """
    command = UpdateMatchStatusCommand(match_id=match_id, status=status)
    try:
        return await service.update_match_status(command)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/match/job/{job_id}", response_model=List[MatchDTO])
async def list_matches_by_job(
    job_id: str,
    status: Optional[str] = None,
    service: MatchApplicationService = Depends(),
):
    """
    按岗位列出匹配记录
    
    获取指定岗位的所有匹配记录。
    
    Args:
        job_id: 岗位ID
        status: 状态过滤（可选）
        service: 匹配应用服务实例
        
    Returns:
        List[MatchDTO]: 匹配记录列表
    """
    return await service.list_matches_by_job(ListMatchesByJobQuery(job_id=job_id, status=status))


@router.get("/match/candidate/{candidate_id}", response_model=List[MatchDTO])
async def list_matches_by_candidate(
    candidate_id: str,
    status: Optional[str] = None,
    service: MatchApplicationService = Depends(),
):
    """
    按候选人列出匹配记录
    
    获取指定候选人的所有匹配记录。
    
    Args:
        candidate_id: 候选人ID
        status: 状态过滤（可选）
        service: 匹配应用服务实例
        
    Returns:
        List[MatchDTO]: 匹配记录列表
    """
    return await service.list_matches_by_candidate(ListMatchesByCandidateQuery(candidate_id=candidate_id, status=status))


# 招聘流程接口
@router.get("/process/{match_id}", response_model=ProcessDTO)
async def get_process(
    match_id: str,
    service: ProcessApplicationService = Depends(),
):
    """
    获取招聘流程
    
    根据匹配ID获取对应的招聘流程信息。
    
    Args:
        match_id: 匹配记录ID
        service: 流程应用服务实例
        
    Returns:
        ProcessDTO: 招聘流程信息
        
    Raises:
        HTTPException: 流程不存在时返回404状态码
    """
    process = await service.get_process(GetProcessQuery(match_id=match_id))
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    return process


@router.post("/process/{match_id}/transition", response_model=ProcessDTO)
async def process_transition(
    match_id: str,
    new_state: str,
    comment: str = "",
    service: ProcessApplicationService = Depends(),
):
    """
    流程状态转换
    
    转换招聘流程的状态，如从待面试转为面试中。
    
    Args:
        match_id: 匹配记录ID
        new_state: 新状态
        comment: 备注说明（可选）
        service: 流程应用服务实例
        
    Returns:
        ProcessDTO: 更新后的流程信息
        
    Raises:
        HTTPException: 状态转换失败时返回400状态码
    """
    command = ProcessTransitionCommand(match_id=match_id, new_state=new_state, comment=comment)
    try:
        return await service.transition(command)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# 搜索接口
@router.post("/search/resume", response_model=List[CandidateDTO])
async def search_resumes(
    company_id: str,
    criteria: Dict[str, Any],
    limit: int = 10,
    service: SearchApplicationService = Depends(),
):
    """
    搜索简历
    
    根据条件搜索候选人简历。
    
    Args:
        company_id: 企业ID
        criteria: 搜索条件
        limit: 返回数量限制，默认为10
        service: 搜索应用服务实例
        
    Returns:
        List[CandidateDTO]: 匹配的候选人列表
    """
    command = SearchResumeCommand(company_id=company_id, criteria=criteria, limit=limit)
    return await service.search_resumes(command)


# 健康检查接口
@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    健康检查
    
    返回服务健康状态。
    
    Returns:
        Dict: 健康状态信息
    """
    return {"status": "healthy", "service": "jobagent"}
