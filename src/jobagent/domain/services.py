from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
from .entities import Job, Candidate, Match
from .repositories import JobRepository, CandidateRepository


class MatchingService(ABC):
    """
    匹配服务接口
    
    定义岗位与候选人匹配相关的标准接口。
    """
    
    @abstractmethod
    async def build_job_profile(self, job: Job) -> Dict[str, Any]:
        """
        构建岗位画像
        
        Args:
            job: 岗位实体
            
        Returns:
            Dict[str, Any]: 岗位画像字典
        """
        pass

    @abstractmethod
    async def build_candidate_profile(self, candidate: Candidate) -> Dict[str, Any]:
        """
        构建候选人画像
        
        Args:
            candidate: 候选人实体
            
        Returns:
            Dict[str, Any]: 候选人画像字典
        """
        pass

    @abstractmethod
    async def calculate_match_score(self, job_profile: Dict[str, Any], candidate_profile: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        计算匹配分数
        
        Args:
            job_profile: 岗位画像
            candidate_profile: 候选人画像
            
        Returns:
            Tuple[float, List[str]]: 匹配分数和匹配理由列表
        """
        pass

    @abstractmethod
    async def match_job_with_candidates(self, job_id: str, top_n: int = 10) -> List[Match]:
        """
        岗位匹配候选人
        
        Args:
            job_id: 岗位ID
            top_n: 返回前N个匹配结果
            
        Returns:
            List[Match]: 匹配结果列表
        """
        pass

    @abstractmethod
    async def match_candidate_with_jobs(self, candidate_id: str, top_n: int = 10) -> List[Match]:
        """
        候选人匹配岗位
        
        Args:
            candidate_id: 候选人ID
            top_n: 返回前N个匹配结果
            
        Returns:
            List[Match]: 匹配结果列表
        """
        pass


class SecurityService(ABC):
    """
    安全服务接口
    
    定义数据加密、脱敏和内容验证相关的标准接口。
    """
    
    @abstractmethod
    def encrypt_data(self, data: str) -> str:
        """
        加密数据
        
        Args:
            data: 待加密的数据
            
        Returns:
            str: 加密后的数据
        """
        pass

    @abstractmethod
    def decrypt_data(self, encrypted_data: str) -> str:
        """
        解密数据
        
        Args:
            encrypted_data: 加密的数据
            
        Returns:
            str: 解密后的数据
        """
        pass

    @abstractmethod
    def mask_phone(self, phone: str) -> str:
        """
        手机号脱敏
        
        Args:
            phone: 原始手机号
            
        Returns:
            str: 脱敏后的手机号
        """
        pass

    @abstractmethod
    def mask_email(self, email: str) -> str:
        """
        邮箱脱敏
        
        Args:
            email: 原始邮箱地址
            
        Returns:
            str: 脱敏后的邮箱
        """
        pass

    @abstractmethod
    def mask_name(self, name: str) -> str:
        """
        姓名脱敏
        
        Args:
            name: 原始姓名
            
        Returns:
            str: 脱敏后的姓名
        """
        pass

    @abstractmethod
    def validate_content(self, content: str) -> Tuple[bool, List[str]]:
        """
        内容安全验证
        
        Args:
            content: 待验证的内容
            
        Returns:
            Tuple[bool, List[str]]: 验证结果和违规信息列表
        """
        pass


class McpProtocolService(ABC):
    """
    MCP协议服务接口
    
    定义与企业和候选人Agent通信的标准接口，实现跨平台Agent互联。
    """
    
    @abstractmethod
    async def call_company_mcp(self, company_id: str, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用企业MCP接口
        
        Args:
            company_id: 企业ID
            action: 操作名称
            payload: 请求参数
            
        Returns:
            Dict[str, Any]: 接口响应
        """
        pass

    @abstractmethod
    async def call_candidate_mcp(self, candidate_id: str, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用候选人MCP接口
        
        Args:
            candidate_id: 候选人ID
            action: 操作名称
            payload: 请求参数
            
        Returns:
            Dict[str, Any]: 接口响应
        """
        pass

    @abstractmethod
    async def fetch_job_list(self, company_id: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        从企业MCP获取岗位列表
        
        Args:
            company_id: 企业ID
            filters: 过滤条件
            
        Returns:
            List[Dict[str, Any]]: 岗位列表
        """
        pass

    @abstractmethod
    async def fetch_candidate_profile(self, candidate_id: str) -> Dict[str, Any]:
        """
        从候选人MCP获取资料
        
        Args:
            candidate_id: 候选人ID
            
        Returns:
            Dict[str, Any]: 候选人资料
        """
        pass


class WeightConfig:
    """
    匹配权重配置
    
    定义匹配算法中各维度的权重系数，权重总和为1。
    """
    
    SKILLS_WEIGHT = 0.35        # 技能匹配权重
    EXPERIENCE_WEIGHT = 0.25    # 经验匹配权重
    EDUCATION_WEIGHT = 0.15     # 学历匹配权重
    LOCATION_WEIGHT = 0.10      # 地点匹配权重
    SALARY_WEIGHT = 0.10        # 薪资匹配权重
    HOT_DEGREE_WEIGHT = 0.05    # 热门程度权重
