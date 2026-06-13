from typing import List, Optional, Dict, Any
from loguru import logger
from ..domain.entities import Company, Job, Candidate, Match, RecruitmentProcess, JobStatus, MatchStatus, ProcessState
from ..domain.repositories import (
    CompanyRepository,
    JobRepository,
    CandidateRepository,
    MatchRepository,
    ProcessRepository,
)
from ..domain.services import MatchingService, SecurityService, McpProtocolService
from .dto import CompanyDTO, JobDTO, CandidateDTO, MatchDTO, ProcessDTO, MatchResultDTO
from .commands import (
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
from .queries import (
    GetCompanyQuery,
    ListCompaniesQuery,
    GetJobQuery,
    ListJobsQuery,
    SearchJobsQuery,
    GetCandidateQuery,
    SearchCandidatesQuery,
    GetMatchQuery,
    ListMatchesByJobQuery,
    ListMatchesByCandidateQuery,
    GetProcessQuery,
)


class CompanyApplicationService:
    """企业应用服务
    
    提供企业管理相关的业务操作。
    """
    
    def __init__(self, company_repo: CompanyRepository):
        """
        初始化企业应用服务
        
        Args:
            company_repo: 企业仓储实例
        """
        self.company_repo = company_repo

    async def create_company(self, command: CreateCompanyCommand) -> CompanyDTO:
        """
        创建企业
        
        Args:
            command: 创建企业命令
            
        Returns:
            CompanyDTO: 创建的企业DTO
        """
        company = Company(
            name=command.name,
            mcp_server_url=command.mcp_server_url,
            api_key=command.api_key,
        )
        saved = await self.company_repo.save(company)
        return CompanyDTO(**saved.__dict__)

    async def update_company(self, command: UpdateCompanyCommand) -> CompanyDTO:
        """
        更新企业信息
        
        Args:
            command: 更新企业命令
            
        Returns:
            CompanyDTO: 更新后的企业DTO
            
        Raises:
            ValueError: 企业不存在时抛出
        """
        company = await self.company_repo.get_by_id(command.company_id)
        if not company:
            raise ValueError("Company not found")
        update_data = {k: v for k, v in command.dict().items() if v is not None and k != "company_id"}
        company.update(**update_data)
        saved = await self.company_repo.save(company)
        return CompanyDTO(**saved.__dict__)

    async def delete_company(self, command: DeleteCompanyCommand) -> bool:
        """
        删除企业
        
        Args:
            command: 删除企业命令
            
        Returns:
            bool: 删除成功返回True
        """
        return await self.company_repo.delete(command.company_id)

    async def get_company(self, query: GetCompanyQuery) -> Optional[CompanyDTO]:
        """
        获取企业详情
        
        Args:
            query: 获取企业查询
            
        Returns:
            Optional[CompanyDTO]: 企业DTO，如果不存在返回None
        """
        company = await self.company_repo.get_by_id(query.company_id)
        return CompanyDTO(**company.__dict__) if company else None

    async def list_companies(self, query: ListCompaniesQuery) -> List[CompanyDTO]:
        """
        列出企业列表
        
        Args:
            query: 列出企业查询
            
        Returns:
            List[CompanyDTO]: 企业DTO列表
        """
        companies = await self.company_repo.list(query.status, query.page, query.size)
        return [CompanyDTO(**c.__dict__) for c in companies]


class JobApplicationService:
    """岗位应用服务
    
    提供岗位管理相关的业务操作。
    """
    
    def __init__(
        self,
        job_repo: JobRepository,
        company_repo: CompanyRepository,
        mcp_service: McpProtocolService,
    ):
        """
        初始化岗位应用服务
        
        Args:
            job_repo: 岗位仓储实例
            company_repo: 企业仓储实例
            mcp_service: MCP协议服务实例
        """
        self.job_repo = job_repo
        self.company_repo = company_repo
        self.mcp_service = mcp_service

    async def create_job(self, command: CreateJobCommand) -> JobDTO:
        """
        创建岗位
        
        Args:
            command: 创建岗位命令
            
        Returns:
            JobDTO: 创建的岗位DTO
            
        Raises:
            ValueError: 企业不存在或未激活时抛出
        """
        company = await self.company_repo.get_by_id(command.company_id)
        if not company or not company.is_active():
            raise ValueError("Company not found or inactive")
        
        job = Job(
            company_id=command.company_id,
            title=command.title,
            description=command.description or "",
            requirements=command.requirements or "",
            location=command.location or "",
            salary_range=command.salary_range or "",
            tags=command.tags or [],
        )
        saved = await self.job_repo.save(job)
        return JobDTO(**saved.__dict__)

    async def update_job(self, command: UpdateJobCommand) -> JobDTO:
        """
        更新岗位信息
        
        Args:
            command: 更新岗位命令
            
        Returns:
            JobDTO: 更新后的岗位DTO
            
        Raises:
            ValueError: 岗位不存在时抛出
        """
        job = await self.job_repo.get_by_id(command.job_id)
        if not job:
            raise ValueError("Job not found")
        update_data = {k: v for k, v in command.dict().items() if v is not None and k != "job_id"}
        if "status" in update_data:
            update_data["status"] = JobStatus(update_data["status"])
        job.update(**update_data)
        saved = await self.job_repo.save(job)
        return JobDTO(**saved.__dict__)

    async def get_job(self, query: GetJobQuery) -> Optional[JobDTO]:
        """
        获取岗位详情
        
        Args:
            query: 获取岗位查询
            
        Returns:
            Optional[JobDTO]: 岗位DTO，如果不存在返回None
        """
        job = await self.job_repo.get_by_id(query.job_id)
        return JobDTO(**job.__dict__) if job else None

    async def list_jobs(self, query: ListJobsQuery) -> List[JobDTO]:
        """
        列出企业岗位列表
        
        Args:
            query: 列出岗位查询
            
        Returns:
            List[JobDTO]: 岗位DTO列表
        """
        jobs = await self.job_repo.list_by_company(
            query.company_id, 
            JobStatus(query.status) if query.status else None
        )
        return [JobDTO(**j.__dict__) for j in jobs]

    async def sync_jobs_from_mcp(self, company_id: str) -> List[JobDTO]:
        """
        从MCP服务器同步岗位数据
        
        Args:
            company_id: 企业ID
            
        Returns:
            List[JobDTO]: 同步后的岗位DTO列表
            
        Raises:
            ValueError: 企业不存在时抛出
        """
        company = await self.company_repo.get_by_id(company_id)
        if not company:
            raise ValueError("Company not found")
        
        job_list = await self.mcp_service.fetch_job_list(company_id)
        created_jobs = []
        
        for job_data in job_list:
            existing_job = await self.job_repo.get_by_id(job_data.get("job_id"))
            if existing_job:
                existing_job.update(**job_data)
                saved = await self.job_repo.save(existing_job)
            else:
                job = Job(
                    company_id=company_id,
                    title=job_data["title"],
                    description=job_data.get("description", ""),
                    requirements=job_data.get("requirements", ""),
                    location=job_data.get("location", ""),
                    salary_range=job_data.get("salary_range", ""),
                    tags=job_data.get("tags", []),
                )
                saved = await self.job_repo.save(job)
            created_jobs.append(JobDTO(**saved.__dict__))
        
        return created_jobs


class CandidateApplicationService:
    """候选人应用服务
    
    提供候选人管理相关的业务操作。
    """
    
    def __init__(
        self,
        candidate_repo: CandidateRepository,
        security_service: SecurityService,
        mcp_service: McpProtocolService,
    ):
        """
        初始化候选人应用服务
        
        Args:
            candidate_repo: 候选人仓储实例
            security_service: 安全服务实例
            mcp_service: MCP协议服务实例
        """
        self.candidate_repo = candidate_repo
        self.security_service = security_service
        self.mcp_service = mcp_service

    async def create_candidate(self, command: CreateCandidateCommand) -> CandidateDTO:
        """
        创建候选人
        
        Args:
            command: 创建候选人命令
            
        Returns:
            CandidateDTO: 创建的候选人DTO
        """
        candidate = Candidate(
            mcp_server_url=command.mcp_server_url,
            api_key=command.api_key,
            name=command.name,
            phone=self.security_service.mask_phone(command.phone) if command.phone else "",
            email=self.security_service.mask_email(command.email) if command.email else "",
            resume_text=command.resume_text,
            skills=command.skills or [],
            experience=command.experience,
            education=command.education,
            job_intent=command.job_intent or {},
        )
        saved = await self.candidate_repo.save(candidate)
        return CandidateDTO(**saved.__dict__)

    async def update_candidate(self, command: UpdateCandidateCommand) -> CandidateDTO:
        """
        更新候选人信息
        
        Args:
            command: 更新候选人命令
            
        Returns:
            CandidateDTO: 更新后的候选人DTO
            
        Raises:
            ValueError: 候选人不存在时抛出
        """
        candidate = await self.candidate_repo.get_by_id(command.candidate_id)
        if not candidate:
            raise ValueError("Candidate not found")
        
        update_data = {k: v for k, v in command.dict().items() if v is not None and k != "candidate_id"}
        if "phone" in update_data:
            update_data["phone"] = self.security_service.mask_phone(update_data["phone"])
        if "email" in update_data:
            update_data["email"] = self.security_service.mask_email(update_data["email"])
        
        candidate.update(**update_data)
        saved = await self.candidate_repo.save(candidate)
        return CandidateDTO(**saved.__dict__)

    async def update_job_intent(self, command: UpdateJobIntentCommand) -> CandidateDTO:
        """
        更新求职意向
        
        Args:
            command: 更新求职意向命令
            
        Returns:
            CandidateDTO: 更新后的候选人DTO
            
        Raises:
            ValueError: 候选人不存在时抛出
        """
        candidate = await self.candidate_repo.get_by_id(command.candidate_id)
        if not candidate:
            raise ValueError("Candidate not found")
        candidate.update_job_intent(command.job_intent)
        saved = await self.candidate_repo.save(candidate)
        return CandidateDTO(**saved.__dict__)

    async def get_candidate(self, query: GetCandidateQuery) -> Optional[CandidateDTO]:
        """
        获取候选人详情
        
        Args:
            query: 获取候选人查询
            
        Returns:
            Optional[CandidateDTO]: 候选人DTO，如果不存在返回None
        """
        candidate = await self.candidate_repo.get_by_id(query.candidate_id)
        return CandidateDTO(**candidate.__dict__) if candidate else None

    async def search_candidates(self, query: SearchCandidatesQuery) -> List[CandidateDTO]:
        """
        搜索候选人
        
        Args:
            query: 搜索候选人查询
            
        Returns:
            List[CandidateDTO]: 匹配的候选人DTO列表
        """
        candidates = await self.candidate_repo.search(query.criteria)
        return [CandidateDTO(**c.__dict__) for c in candidates]

    async def fetch_profile_from_mcp(self, candidate_id: str) -> CandidateDTO:
        """
        从MCP服务器获取候选人资料
        
        Args:
            candidate_id: 候选人ID
            
        Returns:
            CandidateDTO: 更新后的候选人DTO
            
        Raises:
            ValueError: 候选人不存在时抛出
        """
        profile = await self.mcp_service.fetch_candidate_profile(candidate_id)
        candidate = await self.candidate_repo.get_by_id(candidate_id)
        
        if candidate:
            update_data = {
                "name": profile.get("name", ""),
                "phone": self.security_service.mask_phone(profile.get("phone", "")),
                "email": self.security_service.mask_email(profile.get("email", "")),
                "resume_text": profile.get("resume_text", ""),
                "skills": profile.get("skills", []),
                "experience": profile.get("experience", ""),
                "education": profile.get("education", ""),
                "job_intent": profile.get("job_intent", {}),
            }
            candidate.update(**update_data)
            saved = await self.candidate_repo.save(candidate)
        else:
            raise ValueError("Candidate not found")
        
        return CandidateDTO(**saved.__dict__)


class MatchApplicationService:
    """匹配应用服务
    
    提供岗位与候选人匹配相关的业务操作。
    """
    
    def __init__(
        self,
        match_repo: MatchRepository,
        job_repo: JobRepository,
        candidate_repo: CandidateRepository,
        process_repo: ProcessRepository,
        matching_service: MatchingService,
    ):
        """
        初始化匹配应用服务
        
        Args:
            match_repo: 匹配仓储实例
            job_repo: 岗位仓储实例
            candidate_repo: 候选人仓储实例
            process_repo: 流程仓储实例
            matching_service: 匹配服务实例
        """
        self.match_repo = match_repo
        self.job_repo = job_repo
        self.candidate_repo = candidate_repo
        self.process_repo = process_repo
        self.matching_service = matching_service

    async def match_job_with_candidates(self, command: MatchJobCommand) -> List[MatchResultDTO]:
        """
        岗位匹配候选人
        
        Args:
            command: 岗位匹配命令
            
        Returns:
            List[MatchResultDTO]: 匹配结果列表
            
        Raises:
            ValueError: 岗位不存在或未开放时抛出
        """
        job = await self.job_repo.get_by_id(command.job_id)
        if not job or not job.is_open():
            raise ValueError("Job not found or not open")
        
        matches = await self.matching_service.match_job_with_candidates(
            command.job_id, command.top_n
        )
        
        results = []
        for match in matches:
            job_dto = JobDTO(**job.__dict__)
            candidate = await self.candidate_repo.get_by_id(match.candidate_id)
            candidate_dto = CandidateDTO(**candidate.__dict__) if candidate else None
            match_dto = MatchDTO(**match.__dict__)
            
            process = await self.process_repo.get_by_match_id(match.id)
            if not process:
                process = RecruitmentProcess(match_id=match.id)
                await self.process_repo.save(process)
            
            results.append(MatchResultDTO(match=match_dto, job=job_dto, candidate=candidate_dto))
        
        return results

    async def match_candidate_with_jobs(self, command: MatchCandidateCommand) -> List[MatchResultDTO]:
        """
        候选人匹配岗位
        
        Args:
            command: 候选人匹配命令
            
        Returns:
            List[MatchResultDTO]: 匹配结果列表
            
        Raises:
            ValueError: 候选人不存在时抛出
        """
        candidate = await self.candidate_repo.get_by_id(command.candidate_id)
        if not candidate:
            raise ValueError("Candidate not found")
        
        matches = await self.matching_service.match_candidate_with_jobs(
            command.candidate_id, command.top_n
        )
        
        results = []
        for match in matches:
            job = await self.job_repo.get_by_id(match.job_id)
            job_dto = JobDTO(**job.__dict__) if job else None
            candidate_dto = CandidateDTO(**candidate.__dict__)
            match_dto = MatchDTO(**match.__dict__)
            
            process = await self.process_repo.get_by_match_id(match.id)
            if not process:
                process = RecruitmentProcess(match_id=match.id)
                await self.process_repo.save(process)
            
            results.append(MatchResultDTO(match=match_dto, job=job_dto, candidate=candidate_dto))
        
        return results

    async def update_match_status(self, command: UpdateMatchStatusCommand) -> MatchDTO:
        """
        更新匹配状态
        
        Args:
            command: 更新匹配状态命令
            
        Returns:
            MatchDTO: 更新后的匹配DTO
            
        Raises:
            ValueError: 匹配不存在时抛出
        """
        match = await self.match_repo.get_by_id(command.match_id)
        if not match:
            raise ValueError("Match not found")
        
        if command.status == "accepted":
            match.accept()
        elif command.status == "rejected":
            match.reject()
        
        saved = await self.match_repo.save(match)
        return MatchDTO(**saved.__dict__)

    async def get_match(self, query: GetMatchQuery) -> Optional[MatchDTO]:
        """
        获取匹配详情
        
        Args:
            query: 获取匹配查询
            
        Returns:
            Optional[MatchDTO]: 匹配DTO，如果不存在返回None
        """
        match = await self.match_repo.get_by_id(query.match_id)
        return MatchDTO(**match.__dict__) if match else None

    async def list_matches_by_job(self, query: ListMatchesByJobQuery) -> List[MatchDTO]:
        """
        列出岗位的匹配记录
        
        Args:
            query: 列出岗位匹配查询
            
        Returns:
            List[MatchDTO]: 匹配DTO列表
        """
        matches = await self.match_repo.list_by_job(
            query.job_id, 
            MatchStatus(query.status) if query.status else None
        )
        return [MatchDTO(**m.__dict__) for m in matches]

    async def list_matches_by_candidate(self, query: ListMatchesByCandidateQuery) -> List[MatchDTO]:
        """
        列出候选人的匹配记录
        
        Args:
            query: 列出候选人匹配查询
            
        Returns:
            List[MatchDTO]: 匹配DTO列表
        """
        matches = await self.match_repo.list_by_candidate(
            query.candidate_id,
            MatchStatus(query.status) if query.status else None
        )
        return [MatchDTO(**m.__dict__) for m in matches]


class ProcessApplicationService:
    """招聘流程应用服务
    
    提供招聘流程管理相关的业务操作。
    """
    
    def __init__(
        self,
        process_repo: ProcessRepository,
        match_repo: MatchRepository,
        mcp_service: McpProtocolService,
    ):
        """
        初始化招聘流程应用服务
        
        Args:
            process_repo: 流程仓储实例
            match_repo: 匹配仓储实例
            mcp_service: MCP协议服务实例
        """
        self.process_repo = process_repo
        self.match_repo = match_repo
        self.mcp_service = mcp_service

    async def get_process(self, query: GetProcessQuery) -> Optional[ProcessDTO]:
        """
        获取招聘流程
        
        Args:
            query: 获取流程查询
            
        Returns:
            Optional[ProcessDTO]: 流程DTO，如果不存在返回None
        """
        process = await self.process_repo.get_by_match_id(query.match_id)
        if not process:
            return None
        
        history_dto = [
            {"state": h.state.value, "timestamp": h.timestamp, "comment": h.comment}
            for h in process.history
        ]
        
        return ProcessDTO(
            id=process.id,
            match_id=process.match_id,
            current_state=process.current_state.value,
            history=history_dto,
            created_at=process.created_at,
            updated_at=process.updated_at,
        )

    async def transition(self, command: ProcessTransitionCommand) -> ProcessDTO:
        """
        流程状态转换
        
        Args:
            command: 流程转换命令
            
        Returns:
            ProcessDTO: 更新后的流程DTO
            
        Raises:
            ValueError: 流程不存在或转换无效时抛出
        """
        process = await self.process_repo.get_by_match_id(command.match_id)
        if not process:
            raise ValueError("Process not found")
        
        try:
            new_state = ProcessState(command.new_state)
            process.transition(new_state, command.comment)
            saved = await self.process_repo.save(process)
            
            if new_state == ProcessState.RESUME_PUSHED:
                await self.notify_company(command.match_id)
            elif new_state == ProcessState.SCREENING:
                await self.notify_candidate(command.match_id)
            
            history_dto = [
                {"state": h.state.value, "timestamp": h.timestamp, "comment": h.comment}
                for h in saved.history
            ]
            
            return ProcessDTO(
                id=saved.id,
                match_id=saved.match_id,
                current_state=saved.current_state.value,
                history=history_dto,
                created_at=saved.created_at,
                updated_at=saved.updated_at,
            )
        except ValueError as e:
            raise ValueError(f"Invalid transition: {str(e)}")

    async def notify_company(self, match_id: str):
        """
        通知企业
        
        Args:
            match_id: 匹配记录ID
        """
        match = await self.match_repo.get_by_id(match_id)
        if match:
            logger.info(f"Notifying company about match {match_id}")
            await self.mcp_service.call_company_mcp(
                match.job_id,
                "resume_received",
                {"match_id": match_id, "candidate_id": match.candidate_id}
            )

    async def notify_candidate(self, match_id: str):
        """
        通知候选人
        
        Args:
            match_id: 匹配记录ID
        """
        match = await self.match_repo.get_by_id(match_id)
        if match:
            logger.info(f"Notifying candidate about match {match_id}")
            await self.mcp_service.call_candidate_mcp(
                match.candidate_id,
                "screening_started",
                {"match_id": match_id, "job_id": match.job_id}
            )


class SearchApplicationService:
    """搜索应用服务
    
    提供简历搜索相关的业务操作。
    """
    
    def __init__(
        self,
        candidate_repo: CandidateRepository,
        security_service: SecurityService,
    ):
        """
        初始化搜索应用服务
        
        Args:
            candidate_repo: 候选人仓储实例
            security_service: 安全服务实例
        """
        self.candidate_repo = candidate_repo
        self.security_service = security_service

    async def search_resumes(self, command: SearchResumeCommand) -> List[CandidateDTO]:
        """
        搜索简历
        
        Args:
            command: 搜索简历命令
            
        Returns:
            List[CandidateDTO]: 匹配的候选人DTO列表
        """
        candidates = await self.candidate_repo.search(command.criteria)
        limited = candidates[:command.limit]
        return [CandidateDTO(**c.__dict__) for c in limited]
