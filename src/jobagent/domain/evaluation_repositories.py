"""
评价仓储接口

定义企业评价和候选人评价数据访问的标准接口。
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from .enterprise_evaluation import EnterpriseEvaluation, EvaluationReport
from .candidate_evaluation import CandidateEvaluation, CandidateEvaluationReport, InitialScreeningResult, DeepAssessmentResult


class EnterpriseEvaluationRepository(ABC):
    """
    企业评价仓储接口
    
    定义企业评价数据访问的标准接口。
    """
    
    @abstractmethod
    async def save(self, evaluation: EnterpriseEvaluation) -> EnterpriseEvaluation:
        """
        保存企业评价
        
        Args:
            evaluation: 企业评价实体
            
        Returns:
            EnterpriseEvaluation: 保存后的评价实体
        """
        pass

    @abstractmethod
    async def get_by_id(self, evaluation_id: str) -> Optional[EnterpriseEvaluation]:
        """
        根据ID获取企业评价
        
        Args:
            evaluation_id: 评价ID
            
        Returns:
            Optional[EnterpriseEvaluation]: 评价实体，如果不存在返回None
        """
        pass

    @abstractmethod
    async def get_latest_by_company(self, company_id: str) -> Optional[EnterpriseEvaluation]:
        """
        获取企业最新的评价
        
        Args:
            company_id: 企业ID
            
        Returns:
            Optional[EnterpriseEvaluation]: 最新评价实体
        """
        pass

    @abstractmethod
    async def list_by_company(self, company_id: str, limit: int = 10) -> List[EnterpriseEvaluation]:
        """
        列出企业的评价历史
        
        Args:
            company_id: 企业ID
            limit: 返回数量限制
            
        Returns:
            List[EnterpriseEvaluation]: 评价列表
        """
        pass

    @abstractmethod
    async def get_report(self, evaluation_id: str) -> Optional[EvaluationReport]:
        """
        获取评价报告
        
        Args:
            evaluation_id: 评价ID
            
        Returns:
            Optional[EvaluationReport]: 评价报告
        """
        pass

    @abstractmethod
    async def delete(self, evaluation_id: str) -> bool:
        """
        删除企业评价
        
        Args:
            evaluation_id: 评价ID
            
        Returns:
            bool: 删除成功返回True
        """
        pass


class CandidateEvaluationRepository(ABC):
    """
    候选人评价仓储接口
    
    定义候选人评价数据访问的标准接口。
    """
    
    @abstractmethod
    async def save(self, evaluation: CandidateEvaluation) -> CandidateEvaluation:
        """
        保存候选人评价
        
        Args:
            evaluation: 候选人评价实体
            
        Returns:
            CandidateEvaluation: 保存后的评价实体
        """
        pass

    @abstractmethod
    async def get_by_id(self, evaluation_id: str) -> Optional[CandidateEvaluation]:
        """
        根据ID获取候选人评价
        
        Args:
            evaluation_id: 评价ID
            
        Returns:
            Optional[CandidateEvaluation]: 评价实体
        """
        pass

    @abstractmethod
    async def get_latest_by_candidate_job(self, candidate_id: str, job_id: str) -> Optional[CandidateEvaluation]:
        """
        获取特定候选人对特定岗位的最新评价
        
        Args:
            candidate_id: 候选人ID
            job_id: 岗位ID
            
        Returns:
            Optional[CandidateEvaluation]: 评价实体
        """
        pass

    @abstractmethod
    async def list_by_job(self, job_id: str, limit: int = 100) -> List[CandidateEvaluation]:
        """
        列出岗位的所有候选人评价
        
        Args:
            job_id: 岗位ID
            limit: 返回数量限制
            
        Returns:
            List[CandidateEvaluation]: 评价列表
        """
        pass

    @abstractmethod
    async def list_by_candidate(self, candidate_id: str, limit: int = 50) -> List[CandidateEvaluation]:
        """
        列出候选人的所有评价
        
        Args:
            candidate_id: 候选人ID
            limit: 返回数量限制
            
        Returns:
            List[CandidateEvaluation]: 评价列表
        """
        pass

    @abstractmethod
    async def save_initial_screening(self, result: InitialScreeningResult) -> InitialScreeningResult:
        """
        保存初筛结果
        
        Args:
            result: 初筛结果
            
        Returns:
            InitialScreeningResult: 保存后的结果
        """
        pass

    @abstractmethod
    async def save_deep_assessment(self, result: DeepAssessmentResult) -> DeepAssessmentResult:
        """
        保存深度评估结果
        
        Args:
            result: 深度评估结果
            
        Returns:
            DeepAssessmentResult: 保存后的结果
        """
        pass

    @abstractmethod
    async def get_report(self, evaluation_id: str) -> Optional[CandidateEvaluationReport]:
        """
        获取评价报告
        
        Args:
            evaluation_id: 评价ID
            
        Returns:
            Optional[CandidateEvaluationReport]: 评价报告
        """
        pass

    @abstractmethod
    async def delete(self, evaluation_id: str) -> bool:
        """
        删除候选人评价
        
        Args:
            evaluation_id: 评价ID
            
        Returns:
            bool: 删除成功返回True
        """
        pass
