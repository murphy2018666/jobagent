from sqlalchemy import create_engine, Column, String, Text, DateTime, Enum, Float, JSON, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
from ..domain.entities import Company, Job, Candidate, Match, RecruitmentProcess, JobStatus, MatchStatus, ProcessState, ProcessHistory
from ..domain.repositories import (
    CompanyRepository,
    JobRepository,
    CandidateRepository,
    MatchRepository,
    ProcessRepository,
)
from ..config.settings import settings


Base = declarative_base()


class DBCompany(Base):
    """企业数据库模型"""
    __tablename__ = "companies"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    mcp_server_url = Column(String(500), nullable=False)
    api_key = Column(String(255), nullable=False)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    jobs = relationship("DBJob", back_populates="company")


class DBJob(Base):
    """岗位数据库模型"""
    __tablename__ = "jobs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    requirements = Column(Text)
    location = Column(String(100))
    salary_range = Column(String(50))
    tags = Column(JSON)
    status = Column(Enum(JobStatus), default=JobStatus.OPEN)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    company = relationship("DBCompany", back_populates="jobs")


class DBCandidate(Base):
    """候选人数据库模型"""
    __tablename__ = "candidates"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mcp_server_url = Column(String(500), nullable=False)
    api_key = Column(String(255), nullable=False)
    name = Column(String(100))
    phone = Column(String(20))
    email = Column(String(255))
    resume_text = Column(Text)
    skills = Column(JSON)
    experience = Column(String(100))
    education = Column(String(50))
    job_intent = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class DBMatch(Base):
    """匹配记录数据库模型"""
    __tablename__ = "matches"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id"))
    candidate_id = Column(String(36), ForeignKey("candidates.id"))
    score = Column(Float, nullable=False)
    match_reasons = Column(JSON)
    status = Column(Enum(MatchStatus), default=MatchStatus.PENDING)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class DBProcessState(Base):
    """招聘流程状态数据库模型"""
    __tablename__ = "process_states"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    match_id = Column(String(36), ForeignKey("matches.id"), unique=True)
    current_state = Column(Enum(ProcessState), nullable=False)
    history = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class DatabaseCompanyRepository(CompanyRepository):
    """企业仓储数据库实现"""
    
    def __init__(self, session: AsyncSession):
        """
        初始化企业仓储
        
        Args:
            session: SQLAlchemy异步会话
        """
        self.session = session

    async def save(self, company: Company) -> Company:
        """
        保存企业实体到数据库
        
        Args:
            company: 企业实体
            
        Returns:
            Company: 保存后的企业实体
        """
        db_company = DBCompany(
            id=company.id,
            name=company.name,
            mcp_server_url=company.mcp_server_url,
            api_key=company.api_key,
            status=company.status,
            created_at=company.created_at,
            updated_at=company.updated_at,
        )
        self.session.add(db_company)
        await self.session.commit()
        await self.session.refresh(db_company)
        return self._to_domain(db_company)

    async def get_by_id(self, company_id: str) -> Company | None:
        """
        根据ID获取企业
        
        Args:
            company_id: 企业ID
            
        Returns:
            Optional[Company]: 企业实体，如果不存在返回None
        """
        db_company = await self.session.get(DBCompany, company_id)
        return self._to_domain(db_company) if db_company else None

    async def get_by_api_key(self, api_key: str) -> Company | None:
        """
        根据API密钥获取企业
        
        Args:
            api_key: API密钥
            
        Returns:
            Optional[Company]: 企业实体，如果不存在返回None
        """
        result = await self.session.query(DBCompany).filter(DBCompany.api_key == api_key).first()
        return self._to_domain(result) if result else None

    async def list(self, status: str | None = None, page: int = 1, size: int = 20) -> list[Company]:
        """
        列出企业列表
        
        Args:
            status: 状态过滤
            page: 页码
            size: 每页数量
            
        Returns:
            list[Company]: 企业列表
        """
        query = self.session.query(DBCompany)
        if status:
            query = query.filter(DBCompany.status == status)
        query = query.offset((page - 1) * size).limit(size)
        results = await query.all()
        return [self._to_domain(r) for r in results]

    async def delete(self, company_id: str) -> bool:
        """
        删除企业
        
        Args:
            company_id: 企业ID
            
        Returns:
            bool: 删除成功返回True
        """
        db_company = await self.session.get(DBCompany, company_id)
        if db_company:
            await self.session.delete(db_company)
            await self.session.commit()
            return True
        return False

    def _to_domain(self, db_company: DBCompany) -> Company:
        """
        将数据库模型转换为领域实体
        
        Args:
            db_company: 数据库模型
            
        Returns:
            Company: 领域实体
        """
        domain = Company(
            company_id=db_company.id,
            name=db_company.name,
            mcp_server_url=db_company.mcp_server_url,
            api_key=db_company.api_key,
            status=db_company.status,
        )
        domain.created_at = db_company.created_at
        domain.updated_at = db_company.updated_at
        return domain


class DatabaseJobRepository(JobRepository):
    """岗位仓储数据库实现"""
    
    def __init__(self, session: AsyncSession):
        """
        初始化岗位仓储
        
        Args:
            session: SQLAlchemy异步会话
        """
        self.session = session

    async def save(self, job: Job) -> Job:
        """
        保存岗位实体到数据库
        
        Args:
            job: 岗位实体
            
        Returns:
            Job: 保存后的岗位实体
        """
        db_job = DBJob(
            id=job.id,
            company_id=job.company_id,
            title=job.title,
            description=job.description,
            requirements=job.requirements,
            location=job.location,
            salary_range=job.salary_range,
            tags=job.tags,
            status=job.status,
        )
        self.session.add(db_job)
        await self.session.commit()
        await self.session.refresh(db_job)
        return self._to_domain(db_job)

    async def get_by_id(self, job_id: str) -> Job | None:
        """
        根据ID获取岗位
        
        Args:
            job_id: 岗位ID
            
        Returns:
            Optional[Job]: 岗位实体，如果不存在返回None
        """
        db_job = await self.session.get(DBJob, job_id)
        return self._to_domain(db_job) if db_job else None

    async def list_by_company(self, company_id: str, status: JobStatus | None = None) -> list[Job]:
        """
        根据企业ID列出岗位
        
        Args:
            company_id: 企业ID
            status: 状态过滤
            
        Returns:
            list[Job]: 岗位列表
        """
        query = self.session.query(DBJob).filter(DBJob.company_id == company_id)
        if status:
            query = query.filter(DBJob.status == status)
        results = await query.all()
        return [self._to_domain(r) for r in results]

    async def search(self, filters: dict) -> list[Job]:
        """
        搜索岗位
        
        Args:
            filters: 搜索条件字典
            
        Returns:
            list[Job]: 匹配的岗位列表
        """
        query = self.session.query(DBJob)
        if "location" in filters:
            query = query.filter(DBJob.location == filters["location"])
        if "tags" in filters:
            tags = filters["tags"]
            if isinstance(tags, list):
                for tag in tags:
                    query = query.filter(DBJob.tags.contains([tag]))
        results = await query.all()
        return [self._to_domain(r) for r in results]

    async def delete(self, job_id: str) -> bool:
        """
        删除岗位
        
        Args:
            job_id: 岗位ID
            
        Returns:
            bool: 删除成功返回True
        """
        db_job = await self.session.get(DBJob, job_id)
        if db_job:
            await self.session.delete(db_job)
            await self.session.commit()
            return True
        return False

    def _to_domain(self, db_job: DBJob) -> Job:
        """
        将数据库模型转换为领域实体
        
        Args:
            db_job: 数据库模型
            
        Returns:
            Job: 领域实体
        """
        job = Job(
            job_id=db_job.id,
            company_id=db_job.company_id,
            title=db_job.title,
            description=db_job.description,
            requirements=db_job.requirements,
            location=db_job.location,
            salary_range=db_job.salary_range,
            tags=db_job.tags or [],
            status=db_job.status,
        )
        job.created_at = db_job.created_at
        job.updated_at = db_job.updated_at
        return job


class DatabaseCandidateRepository(CandidateRepository):
    """候选人仓储数据库实现"""
    
    def __init__(self, session: AsyncSession):
        """
        初始化候选人仓储
        
        Args:
            session: SQLAlchemy异步会话
        """
        self.session = session

    async def save(self, candidate: Candidate) -> Candidate:
        """
        保存候选人实体到数据库
        
        Args:
            candidate: 候选人实体
            
        Returns:
            Candidate: 保存后的候选人实体
        """
        db_candidate = DBCandidate(
            id=candidate.id,
            mcp_server_url=candidate.mcp_server_url,
            api_key=candidate.api_key,
            name=candidate.name,
            phone=candidate.phone,
            email=candidate.email,
            resume_text=candidate.resume_text,
            skills=candidate.skills,
            experience=candidate.experience,
            education=candidate.education,
            job_intent=candidate.job_intent,
        )
        self.session.add(db_candidate)
        await self.session.commit()
        await self.session.refresh(db_candidate)
        return self._to_domain(db_candidate)

    async def get_by_id(self, candidate_id: str) -> Candidate | None:
        """
        根据ID获取候选人
        
        Args:
            candidate_id: 候选人ID
            
        Returns:
            Optional[Candidate]: 候选人实体，如果不存在返回None
        """
        db_candidate = await self.session.get(DBCandidate, candidate_id)
        return self._to_domain(db_candidate) if db_candidate else None

    async def get_by_api_key(self, api_key: str) -> Candidate | None:
        """
        根据API密钥获取候选人
        
        Args:
            api_key: API密钥
            
        Returns:
            Optional[Candidate]: 候选人实体，如果不存在返回None
        """
        result = await self.session.query(DBCandidate).filter(DBCandidate.api_key == api_key).first()
        return self._to_domain(result) if result else None

    async def search(self, criteria: dict) -> list[Candidate]:
        """
        搜索候选人
        
        Args:
            criteria: 搜索条件字典
            
        Returns:
            list[Candidate]: 匹配的候选人列表
        """
        query = self.session.query(DBCandidate)
        if "skills" in criteria:
            skills = criteria["skills"]
            if isinstance(skills, list):
                for skill in skills:
                    query = query.filter(DBCandidate.skills.contains([skill]))
        if "experience" in criteria:
            query = query.filter(DBCandidate.experience == criteria["experience"])
        if "education" in criteria:
            query = query.filter(DBCandidate.education == criteria["education"])
        if "location" in criteria:
            query = query.filter(DBCandidate.job_intent["location"].astext.contains(criteria["location"]))
        results = await query.all()
        return [self._to_domain(r) for r in results]

    async def update(self, candidate: Candidate) -> Candidate:
        """
        更新候选人实体
        
        Args:
            candidate: 候选人实体
            
        Returns:
            Candidate: 更新后的候选人实体
        """
        return await self.save(candidate)

    def _to_domain(self, db_candidate: DBCandidate) -> Candidate:
        """
        将数据库模型转换为领域实体
        
        Args:
            db_candidate: 数据库模型
            
        Returns:
            Candidate: 领域实体
        """
        candidate = Candidate(
            candidate_id=db_candidate.id,
            mcp_server_url=db_candidate.mcp_server_url,
            api_key=db_candidate.api_key,
            name=db_candidate.name,
            phone=db_candidate.phone,
            email=db_candidate.email,
            resume_text=db_candidate.resume_text,
            skills=db_candidate.skills or [],
            experience=db_candidate.experience,
            education=db_candidate.education,
            job_intent=db_candidate.job_intent or {},
        )
        candidate.created_at = db_candidate.created_at
        candidate.updated_at = db_candidate.updated_at
        return candidate


class DatabaseMatchRepository(MatchRepository):
    """匹配仓储数据库实现"""
    
    def __init__(self, session: AsyncSession):
        """
        初始化匹配仓储
        
        Args:
            session: SQLAlchemy异步会话
        """
        self.session = session

    async def save(self, match: Match) -> Match:
        """
        保存匹配实体到数据库
        
        Args:
            match: 匹配实体
            
        Returns:
            Match: 保存后的匹配实体
        """
        db_match = DBMatch(
            id=match.id,
            job_id=match.job_id,
            candidate_id=match.candidate_id,
            score=match.score,
            match_reasons=match.match_reasons,
            status=match.status,
        )
        self.session.add(db_match)
        await self.session.commit()
        await self.session.refresh(db_match)
        return self._to_domain(db_match)

    async def get_by_id(self, match_id: str) -> Match | None:
        """
        根据ID获取匹配记录
        
        Args:
            match_id: 匹配记录ID
            
        Returns:
            Optional[Match]: 匹配实体，如果不存在返回None
        """
        db_match = await self.session.get(DBMatch, match_id)
        return self._to_domain(db_match) if db_match else None

    async def list_by_job(self, job_id: str, status: MatchStatus | None = None) -> list[Match]:
        """
        根据岗位ID列出匹配记录
        
        Args:
            job_id: 岗位ID
            status: 状态过滤
            
        Returns:
            list[Match]: 匹配记录列表，按分数降序排列
        """
        query = self.session.query(DBMatch).filter(DBMatch.job_id == job_id)
        if status:
            query = query.filter(DBMatch.status == status)
        results = await query.order_by(DBMatch.score.desc()).all()
        return [self._to_domain(r) for r in results]

    async def list_by_candidate(self, candidate_id: str, status: MatchStatus | None = None) -> list[Match]:
        """
        根据候选人ID列出匹配记录
        
        Args:
            candidate_id: 候选人ID
            status: 状态过滤
            
        Returns:
            list[Match]: 匹配记录列表，按分数降序排列
        """
        query = self.session.query(DBMatch).filter(DBMatch.candidate_id == candidate_id)
        if status:
            query = query.filter(DBMatch.status == status)
        results = await query.order_by(DBMatch.score.desc()).all()
        return [self._to_domain(r) for r in results]

    async def update_status(self, match_id: str, status: MatchStatus) -> bool:
        """
        更新匹配状态
        
        Args:
            match_id: 匹配记录ID
            status: 新状态
            
        Returns:
            bool: 更新成功返回True
        """
        db_match = await self.session.get(DBMatch, match_id)
        if db_match:
            db_match.status = status
            await self.session.commit()
            return True
        return False

    async def delete(self, match_id: str) -> bool:
        """
        删除匹配记录
        
        Args:
            match_id: 匹配记录ID
            
        Returns:
            bool: 删除成功返回True
        """
        db_match = await self.session.get(DBMatch, match_id)
        if db_match:
            await self.session.delete(db_match)
            await self.session.commit()
            return True
        return False

    def _to_domain(self, db_match: DBMatch) -> Match:
        """
        将数据库模型转换为领域实体
        
        Args:
            db_match: 数据库模型
            
        Returns:
            Match: 领域实体
        """
        match = Match(
            match_id=db_match.id,
            job_id=db_match.job_id,
            candidate_id=db_match.candidate_id,
            score=db_match.score,
            match_reasons=db_match.match_reasons or [],
            status=db_match.status,
        )
        match.created_at = db_match.created_at
        match.updated_at = db_match.updated_at
        return match


class DatabaseProcessRepository(ProcessRepository):
    """招聘流程仓储数据库实现"""
    
    def __init__(self, session: AsyncSession):
        """
        初始化招聘流程仓储
        
        Args:
            session: SQLAlchemy异步会话
        """
        self.session = session

    async def save(self, process: RecruitmentProcess) -> RecruitmentProcess:
        """
        保存招聘流程实体到数据库
        
        Args:
            process: 招聘流程实体
            
        Returns:
            RecruitmentProcess: 保存后的招聘流程实体
        """
        history_data = [
            {"state": h.state.value, "timestamp": h.timestamp.isoformat(), "comment": h.comment}
            for h in process.history
        ]
        
        db_process = DBProcessState(
            id=process.id,
            match_id=process.match_id,
            current_state=process.current_state,
            history=history_data,
        )
        self.session.add(db_process)
        await self.session.commit()
        await self.session.refresh(db_process)
        return self._to_domain(db_process)

    async def get_by_id(self, process_id: str) -> RecruitmentProcess | None:
        """
        根据ID获取招聘流程
        
        Args:
            process_id: 流程ID
            
        Returns:
            Optional[RecruitmentProcess]: 招聘流程实体，如果不存在返回None
        """
        db_process = await self.session.get(DBProcessState, process_id)
        return self._to_domain(db_process) if db_process else None

    async def get_by_match_id(self, match_id: str) -> RecruitmentProcess | None:
        """
        根据匹配ID获取招聘流程
        
        Args:
            match_id: 匹配记录ID
            
        Returns:
            Optional[RecruitmentProcess]: 招聘流程实体，如果不存在返回None
        """
        result = await self.session.query(DBProcessState).filter(DBProcessState.match_id == match_id).first()
        return self._to_domain(result) if result else None

    async def update_state(self, process_id: str, new_state: str, comment: str = "") -> bool:
        """
        更新流程状态
        
        Args:
            process_id: 流程ID
            new_state: 新状态
            comment: 备注说明
            
        Returns:
            bool: 更新成功返回True
        """
        db_process = await self.session.get(DBProcessState, process_id)
        if db_process:
            db_process.current_state = ProcessState(new_state)
            history_data = db_process.history or []
            history_data.append({
                "state": new_state,
                "timestamp": datetime.now().isoformat(),
                "comment": comment,
            })
            db_process.history = history_data
            await self.session.commit()
            return True
        return False

    def _to_domain(self, db_process: DBProcessState) -> RecruitmentProcess:
        """
        将数据库模型转换为领域实体
        
        Args:
            db_process: 数据库模型
            
        Returns:
            RecruitmentProcess: 领域实体
        """
        history = []
        for h in db_process.history or []:
            history.append(ProcessHistory(
                state=ProcessState(h["state"]),
                timestamp=datetime.fromisoformat(h["timestamp"]),
                comment=h.get("comment", ""),
            ))
        
        process = RecruitmentProcess(
            process_id=db_process.id,
            match_id=db_process.match_id,
            current_state=db_process.current_state,
        )
        process.history = history
        process.created_at = db_process.created_at
        process.updated_at = db_process.updated_at
        return process


# 全局数据库引擎和会话配置
engine = create_async_engine(settings.DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncSession:
    """
    获取数据库会话
    
    Yields:
        AsyncSession: SQLAlchemy异步会话
    """
    async with async_session() as session:
        yield session


async def init_db():
    """
    初始化数据库表
    
    创建所有定义的数据库表
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
