import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum


class JobStatus(str, Enum):
    """岗位状态枚举"""
    OPEN = "open"      # 开放状态，可接收候选人申请
    CLOSED = "closed"  # 关闭状态，不再接受申请


class Company:
    """企业实体类
    
    代表一个接入平台的企业，包含企业基本信息和MCP协议配置。
    """
    
    def __init__(
        self,
        name: str,
        mcp_server_url: str,
        api_key: str,
        status: str = "active",
        company_id: Optional[str] = None,
    ):
        """
        初始化企业实体
        
        Args:
            name: 企业名称
            mcp_server_url: MCP服务器地址
            api_key: API密钥
            status: 企业状态，默认为'active'
            company_id: 企业唯一标识，不传则自动生成UUID
        """
        self.id = company_id or str(uuid.uuid4())
        self.name = name
        self.mcp_server_url = mcp_server_url
        self.api_key = api_key
        self.status = status
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def update(self, **kwargs):
        """
        更新企业信息
        
        Args:
            **kwargs: 要更新的属性键值对
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()

    def is_active(self) -> bool:
        """
        检查企业是否处于活跃状态
        
        Returns:
            bool: 活跃状态返回True，否则返回False
        """
        return self.status == "active"


class Job:
    """岗位实体类
    
    代表一个招聘岗位，包含岗位基本信息和要求。
    """
    
    def __init__(
        self,
        company_id: str,
        title: str,
        description: str = "",
        requirements: str = "",
        location: str = "",
        salary_range: str = "",
        tags: Optional[List[str]] = None,
        status: JobStatus = JobStatus.OPEN,
        job_id: Optional[str] = None,
    ):
        """
        初始化岗位实体
        
        Args:
            company_id: 所属企业ID
            title: 岗位名称
            description: 岗位描述
            requirements: 任职要求
            location: 工作地点
            salary_range: 薪资范围
            tags: 岗位标签列表
            status: 岗位状态，默认为OPEN
            job_id: 岗位唯一标识，不传则自动生成UUID
        """
        self.id = job_id or str(uuid.uuid4())
        self.company_id = company_id
        self.title = title
        self.description = description
        self.requirements = requirements
        self.location = location
        self.salary_range = salary_range
        self.tags = tags or []
        self.status = status
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def close(self):
        """
        关闭岗位
        
        将岗位状态设置为CLOSED，不再接受候选人申请
        """
        self.status = JobStatus.CLOSED
        self.updated_at = datetime.now()

    def is_open(self) -> bool:
        """
        检查岗位是否开放
        
        Returns:
            bool: 开放状态返回True，否则返回False
        """
        return self.status == JobStatus.OPEN


class Candidate:
    """候选人实体类
    
    代表一个求职者，包含个人信息、技能和求职意向。
    """
    
    def __init__(
        self,
        mcp_server_url: str,
        api_key: str,
        name: str = "",
        phone: str = "",
        email: str = "",
        resume_text: str = "",
        skills: Optional[List[str]] = None,
        experience: str = "",
        education: str = "",
        job_intent: Optional[Dict[str, Any]] = None,
        candidate_id: Optional[str] = None,
    ):
        """
        初始化候选人实体
        
        Args:
            mcp_server_url: MCP服务器地址
            api_key: API密钥
            name: 候选人姓名
            phone: 联系电话
            email: 邮箱地址
            resume_text: 简历文本内容
            skills: 技能标签列表
            experience: 工作经验描述
            education: 学历信息
            job_intent: 求职意向字典
            candidate_id: 候选人唯一标识，不传则自动生成UUID
        """
        self.id = candidate_id or str(uuid.uuid4())
        self.mcp_server_url = mcp_server_url
        self.api_key = api_key
        self.name = name
        self.phone = phone
        self.email = email
        self.resume_text = resume_text
        self.skills = skills or []
        self.experience = experience
        self.education = education
        self.job_intent = job_intent or {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def update_job_intent(self, intent: Dict[str, Any]):
        """
        更新求职意向
        
        Args:
            intent: 新的求职意向字典
        """
        self.job_intent = intent
        self.updated_at = datetime.now()

    def add_skill(self, skill: str):
        """
        添加技能
        
        Args:
            skill: 技能名称
        """
        if skill not in self.skills:
            self.skills.append(skill)
            self.updated_at = datetime.now()


class MatchStatus(str, Enum):
    """匹配状态枚举"""
    PENDING = "pending"   # 待处理
    ACCEPTED = "accepted" # 已接受
    REJECTED = "rejected" # 已拒绝


class Match:
    """匹配实体类
    
    代表岗位与候选人之间的匹配关系，包含匹配分数和理由。
    """
    
    def __init__(
        self,
        job_id: str,
        candidate_id: str,
        score: float,
        match_reasons: Optional[List[str]] = None,
        status: MatchStatus = MatchStatus.PENDING,
        match_id: Optional[str] = None,
    ):
        """
        初始化匹配实体
        
        Args:
            job_id: 岗位ID
            candidate_id: 候选人ID
            score: 匹配分数（0-1）
            match_reasons: 匹配理由列表
            status: 匹配状态，默认为PENDING
            match_id: 匹配记录唯一标识，不传则自动生成UUID
        """
        self.id = match_id or str(uuid.uuid4())
        self.job_id = job_id
        self.candidate_id = candidate_id
        self.score = score
        self.match_reasons = match_reasons or []
        self.status = status
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def accept(self):
        """
        接受匹配
        
        将匹配状态设置为ACCEPTED
        """
        self.status = MatchStatus.ACCEPTED
        self.updated_at = datetime.now()

    def reject(self):
        """
        拒绝匹配
        
        将匹配状态设置为REJECTED
        """
        self.status = MatchStatus.REJECTED
        self.updated_at = datetime.now()

    def is_pending(self) -> bool:
        """
        检查匹配是否待处理
        
        Returns:
            bool: 待处理状态返回True，否则返回False
        """
        return self.status == MatchStatus.PENDING


class ProcessState(str, Enum):
    """招聘流程状态枚举"""
    JOB_POSTED = "job_posted"           # 岗位发布
    RESUME_PUSHED = "resume_pushed"     # 简历已推送
    SCREENING = "screening"             # 初筛中
    INTERVIEW_SCHEDULED = "interview_scheduled"  # 面试已安排
    OFFER = "offer"                     # 发放offer
    ACCEPTED = "accepted"               # 候选人接受
    REJECTED = "rejected"               # 已拒绝


class ProcessHistory:
    """流程历史记录类
    
    记录招聘流程状态变更的历史。
    """
    
    def __init__(self, state: ProcessState, timestamp: datetime, comment: str = ""):
        """
        初始化流程历史记录
        
        Args:
            state: 流程状态
            timestamp: 时间戳
            comment: 备注说明
        """
        self.state = state
        self.timestamp = timestamp
        self.comment = comment


class RecruitmentProcess:
    """招聘流程实体类
    
    管理单个匹配的招聘流程状态转换。
    """
    
    def __init__(
        self,
        match_id: str,
        current_state: ProcessState = ProcessState.JOB_POSTED,
        process_id: Optional[str] = None,
    ):
        """
        初始化招聘流程实体
        
        Args:
            match_id: 关联的匹配记录ID
            current_state: 当前流程状态，默认为JOB_POSTED
            process_id: 流程唯一标识，不传则自动生成UUID
        """
        self.id = process_id or str(uuid.uuid4())
        self.match_id = match_id
        self.current_state = current_state
        self.history: List[ProcessHistory] = [
            ProcessHistory(state=current_state, timestamp=datetime.now())
        ]
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def transition(self, new_state: ProcessState, comment: str = ""):
        """
        流程状态转换
        
        根据预定义的状态转换规则，将流程从当前状态转换到新状态。
        
        Args:
            new_state: 目标状态
            comment: 转换备注
            
        Raises:
            ValueError: 当转换无效时抛出异常
        """
        valid_transitions = {
            ProcessState.JOB_POSTED: [ProcessState.RESUME_PUSHED],
            ProcessState.RESUME_PUSHED: [ProcessState.SCREENING],
            ProcessState.SCREENING: [ProcessState.INTERVIEW_SCHEDULED, ProcessState.REJECTED],
            ProcessState.INTERVIEW_SCHEDULED: [ProcessState.OFFER, ProcessState.REJECTED],
            ProcessState.OFFER: [ProcessState.ACCEPTED, ProcessState.REJECTED],
        }
        
        if new_state not in valid_transitions.get(self.current_state, []):
            raise ValueError(f"Invalid transition from {self.current_state} to {new_state}")
        
        self.current_state = new_state
        self.history.append(ProcessHistory(state=new_state, timestamp=datetime.now(), comment=comment))
        self.updated_at = datetime.now()
