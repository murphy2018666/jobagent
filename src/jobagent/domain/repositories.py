from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from .entities import Company, Job, Candidate, Match, RecruitmentProcess, JobStatus, MatchStatus


class CompanyRepository(ABC):
    """企业仓储接口
    
    定义企业数据访问的标准接口。
    """
    
    @abstractmethod
    async def save(self, company: Company) -> Company:
        """
        保存企业实体
        
        Args:
            company: 企业实体对象
            
        Returns:
            Company: 保存后的企业实体
        """
        pass

    @abstractmethod
    async def get_by_id(self, company_id: str) -> Optional[Company]:
        """
        根据ID获取企业
        
        Args:
            company_id: 企业ID
            
        Returns:
            Optional[Company]: 企业实体，如果不存在返回None
        """
        pass

    @abstractmethod
    async def get_by_api_key(self, api_key: str) -> Optional[Company]:
        """
        根据API密钥获取企业
        
        Args:
            api_key: API密钥
            
        Returns:
            Optional[Company]: 企业实体，如果不存在返回None
        """
        pass

    @abstractmethod
    async def list(self, status: Optional[str] = None, page: int = 1, size: int = 20) -> List[Company]:
        """
        列出企业列表
        
        Args:
            status: 企业状态过滤（可选）
            page: 页码，默认为1
            size: 每页数量，默认为20
            
        Returns:
            List[Company]: 企业列表
        """
        pass

    @abstractmethod
    async def delete(self, company_id: str) -> bool:
        """
        删除企业
        
        Args:
            company_id: 企业ID
            
        Returns:
            bool: 删除成功返回True，否则返回False
        """
        pass


class JobRepository(ABC):
    """岗位仓储接口
    
    定义岗位数据访问的标准接口。
    """
    
    @abstractmethod
    async def save(self, job: Job) -> Job:
        """
        保存岗位实体
        
        Args:
            job: 岗位实体对象
            
        Returns:
            Job: 保存后的岗位实体
        """
        pass

    @abstractmethod
    async def get_by_id(self, job_id: str) -> Optional[Job]:
        """
        根据ID获取岗位
        
        Args:
            job_id: 岗位ID
            
        Returns:
            Optional[Job]: 岗位实体，如果不存在返回None
        """
        pass

    @abstractmethod
    async def list_by_company(self, company_id: str, status: Optional[JobStatus] = None) -> List[Job]:
        """
        根据企业ID列出岗位
        
        Args:
            company_id: 企业ID
            status: 岗位状态过滤（可选）
            
        Returns:
            List[Job]: 岗位列表
        """
        pass

    @abstractmethod
    async def search(self, filters: Dict[str, Any]) -> List[Job]:
        """
        搜索岗位
        
        Args:
            filters: 搜索条件字典
            
        Returns:
            List[Job]: 匹配的岗位列表
        """
        pass

    @abstractmethod
    async def delete(self, job_id: str) -> bool:
        """
        删除岗位
        
        Args:
            job_id: 岗位ID
            
        Returns:
            bool: 删除成功返回True，否则返回False
        """
        pass


class CandidateRepository(ABC):
    """候选人仓储接口
    
    定义候选人数据访问的标准接口。
    """
    
    @abstractmethod
    async def save(self, candidate: Candidate) -> Candidate:
        """
        保存候选人实体
        
        Args:
            candidate: 候选人实体对象
            
        Returns:
            Candidate: 保存后的候选人实体
        """
        pass

    @abstractmethod
    async def get_by_id(self, candidate_id: str) -> Optional[Candidate]:
        """
        根据ID获取候选人
        
        Args:
            candidate_id: 候选人ID
            
        Returns:
            Optional[Candidate]: 候选人实体，如果不存在返回None
        """
        pass

    @abstractmethod
    async def get_by_api_key(self, api_key: str) -> Optional[Candidate]:
        """
        根据API密钥获取候选人
        
        Args:
            api_key: API密钥
            
        Returns:
            Optional[Candidate]: 候选人实体，如果不存在返回None
        """
        pass

    @abstractmethod
    async def search(self, criteria: Dict[str, Any]) -> List[Candidate]:
        """
        搜索候选人
        
        Args:
            criteria: 搜索条件字典
            
        Returns:
            List[Candidate]: 匹配的候选人列表
        """
        pass

    @abstractmethod
    async def update(self, candidate: Candidate) -> Candidate:
        """
        更新候选人实体
        
        Args:
            candidate: 候选人实体对象
            
        Returns:
            Candidate: 更新后的候选人实体
        """
        pass


class MatchRepository(ABC):
    """匹配仓储接口
    
    定义匹配数据访问的标准接口。
    """
    
    @abstractmethod
    async def save(self, match: Match) -> Match:
        """
        保存匹配实体
        
        Args:
            match: 匹配实体对象
            
        Returns:
            Match: 保存后的匹配实体
        """
        pass

    @abstractmethod
    async def get_by_id(self, match_id: str) -> Optional[Match]:
        """
        根据ID获取匹配记录
        
        Args:
            match_id: 匹配记录ID
            
        Returns:
            Optional[Match]: 匹配实体，如果不存在返回None
        """
        pass

    @abstractmethod
    async def list_by_job(self, job_id: str, status: Optional[MatchStatus] = None) -> List[Match]:
        """
        根据岗位ID列出匹配记录
        
        Args:
            job_id: 岗位ID
            status: 匹配状态过滤（可选）
            
        Returns:
            List[Match]: 匹配记录列表
        """
        pass

    @abstractmethod
    async def list_by_candidate(self, candidate_id: str, status: Optional[MatchStatus] = None) -> List[Match]:
        """
        根据候选人ID列出匹配记录
        
        Args:
            candidate_id: 候选人ID
            status: 匹配状态过滤（可选）
            
        Returns:
            List[Match]: 匹配记录列表
        """
        pass

    @abstractmethod
    async def update_status(self, match_id: str, status: MatchStatus) -> bool:
        """
        更新匹配状态
        
        Args:
            match_id: 匹配记录ID
            status: 新状态
            
        Returns:
            bool: 更新成功返回True，否则返回False
        """
        pass

    @abstractmethod
    async def delete(self, match_id: str) -> bool:
        """
        删除匹配记录
        
        Args:
            match_id: 匹配记录ID
            
        Returns:
            bool: 删除成功返回True，否则返回False
        """
        pass


class ProcessRepository(ABC):
    """招聘流程仓储接口
    
    定义招聘流程数据访问的标准接口。
    """
    
    @abstractmethod
    async def save(self, process: RecruitmentProcess) -> RecruitmentProcess:
        """
        保存招聘流程实体
        
        Args:
            process: 招聘流程实体对象
            
        Returns:
            RecruitmentProcess: 保存后的招聘流程实体
        """
        pass

    @abstractmethod
    async def get_by_id(self, process_id: str) -> Optional[RecruitmentProcess]:
        """
        根据ID获取招聘流程
        
        Args:
            process_id: 流程ID
            
        Returns:
            Optional[RecruitmentProcess]: 招聘流程实体，如果不存在返回None
        """
        pass

    @abstractmethod
    async def get_by_match_id(self, match_id: str) -> Optional[RecruitmentProcess]:
        """
        根据匹配ID获取招聘流程
        
        Args:
            match_id: 匹配记录ID
            
        Returns:
            Optional[RecruitmentProcess]: 招聘流程实体，如果不存在返回None
        """
        pass

    @abstractmethod
    async def update_state(self, process_id: str, new_state: str, comment: str = "") -> bool:
        """
        更新流程状态
        
        Args:
            process_id: 流程ID
            new_state: 新状态
            comment: 备注说明（可选）
            
        Returns:
            bool: 更新成功返回True，否则返回False
        """
        pass
