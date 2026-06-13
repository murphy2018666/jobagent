"""
评价模块应用服务

提供企业评价和候选人评价的业务层接口。
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..domain.repositories import CompanyRepository
from ..domain.entities import Candidate, Job
from ..domain.evaluation_repositories import (
    EnterpriseEvaluationRepository,
    CandidateEvaluationRepository
)
from ..domain.enterprise_evaluation import (
    EnterpriseEvaluation, EvaluationReport
)
from ..domain.candidate_evaluation import (
    CandidateEvaluation, CandidateEvaluationReport
)
from ..infrastructure.enterprise_evaluator import EnterpriseEvaluationService
from ..infrastructure.candidate_evaluator import CandidateEvaluationService


class EnterpriseEvaluationApplicationService:
    """
    企业评价应用服务
    
    提供企业评价的业务操作接口。
    """
    
    def __init__(
        self,
        company_repo: Optional[CompanyRepository] = None,
        evaluation_repo: Optional[EnterpriseEvaluationRepository] = None
    ):
        """
        初始化企业评价应用服务
        
        Args:
            company_repo: 企业仓储实例（可选）
            evaluation_repo: 企业评价仓储实例（可选）
        """
        self._company_repo = company_repo
        self._evaluation_repo = evaluation_repo
        self._service = None
    
    def _get_service(self) -> EnterpriseEvaluationService:
        """获取或创建服务实例"""
        if self._service is None:
            from ..infrastructure.database import (
                DatabaseCompanyRepository,
                DatabaseEnterpriseEvaluationRepository
            )
            company_repo = self._company_repo or DatabaseCompanyRepository()
            evaluation_repo = self._evaluation_repo or DatabaseEnterpriseEvaluationRepository()
            self._service = EnterpriseEvaluationService(company_repo, evaluation_repo)
        return self._service
    
    async def evaluate_company(
        self,
        company_id: str,
        company_data: Dict[str, Any],
        financial_data: Optional[Dict[str, Any]] = None,
        industry_data: Optional[Dict[str, Any]] = None
    ) -> EnterpriseEvaluation:
        """
        执行企业综合评价
        
        Args:
            company_id: 企业ID
            company_data: 企业基本信息和发展数据
            financial_data: 财务数据（可选）
            industry_data: 行业数据（可选）
            
        Returns:
            EnterpriseEvaluation: 综合评价结果
        """
        service = self._get_service()
        return await service.evaluate_company(
            company_id=company_id,
            company_data=company_data,
            financial_data=financial_data,
            industry_data=industry_data
        )
    
    async def get_latest_evaluation(self, company_id: str) -> Optional[EnterpriseEvaluation]:
        """
        获取企业最新评价
        
        Args:
            company_id: 企业ID
            
        Returns:
            Optional[EnterpriseEvaluation]: 最新评价
        """
        service = self._get_service()
        return await service.get_latest_evaluation(company_id)
    
    async def get_evaluation_history(
        self,
        company_id: str,
        limit: int = 10
    ) -> List[EnterpriseEvaluation]:
        """
        获取企业评价历史
        
        Args:
            company_id: 企业ID
            limit: 返回数量限制
            
        Returns:
            List[EnterpriseEvaluation]: 评价历史列表
        """
        service = self._get_service()
        repo = self._evaluation_repo
        
        if repo is None:
            from ..infrastructure.database import DatabaseEnterpriseEvaluationRepository
            repo = DatabaseEnterpriseEvaluationRepository()
        
        return await repo.list_by_company(company_id, limit)
    
    async def generate_report(self, evaluation_id: str) -> Optional[EvaluationReport]:
        """
        生成评价报告
        
        Args:
            evaluation_id: 评价ID
            
        Returns:
            Optional[EvaluationReport]: 评价报告
        """
        service = self._get_service()
        return await service.generate_report(evaluation_id)


class CandidateEvaluationApplicationService:
    """
    候选人评价应用服务
    
    提供候选人评价的业务操作接口。
    """
    
    def __init__(
        self,
        candidate_repo: Optional[CandidateRepository] = None,
        job_repo: Optional[Any] = None,
        evaluation_repo: Optional[CandidateEvaluationRepository] = None
    ):
        """
        初始化候选人评价应用服务
        
        Args:
            candidate_repo: 候选人仓储实例（可选）
            job_repo: 岗位仓储实例（可选）
            evaluation_repo: 候选人评价仓储实例（可选）
        """
        self._candidate_repo = candidate_repo
        self._job_repo = job_repo
        self._evaluation_repo = evaluation_repo
        self._service = None
    
    def _get_service(self) -> CandidateEvaluationService:
        """获取或创建服务实例"""
        if self._service is None:
            from ..infrastructure.database import (
                DatabaseCandidateRepository,
                DatabaseJobRepository,
                DatabaseCandidateEvaluationRepository
            )
            candidate_repo = self._candidate_repo or DatabaseCandidateRepository()
            job_repo = self._job_repo or DatabaseJobRepository()
            evaluation_repo = self._evaluation_repo or DatabaseCandidateEvaluationRepository()
            self._service = CandidateEvaluationService(
                candidate_repo, job_repo, evaluation_repo
            )
        return self._service
    
    async def evaluate_candidate(
        self,
        candidate_id: str,
        job_id: str,
        perform_deep_assessment: bool = True
    ) -> CandidateEvaluation:
        """
        执行候选人综合评价
        
        Args:
            candidate_id: 候选人ID
            job_id: 岗位ID
            perform_deep_assessment: 是否执行深度评估
            
        Returns:
            CandidateEvaluation: 综合评价结果
        """
        service = self._get_service()
        return await service.evaluate_candidate(
            candidate_id=candidate_id,
            job_id=job_id,
            perform_deep_assessment=perform_deep_assessment
        )
    
    async def get_evaluation(self, evaluation_id: str) -> Optional[CandidateEvaluation]:
        """
        获取评价结果
        
        Args:
            evaluation_id: 评价ID
            
        Returns:
            Optional[CandidateEvaluation]: 评价结果
        """
        service = self._get_service()
        return await service.get_evaluation(evaluation_id)
    
    async def get_job_evaluations(
        self,
        job_id: str,
        limit: int = 100
    ) -> List[CandidateEvaluation]:
        """
        获取岗位的所有候选人评价
        
        Args:
            job_id: 岗位ID
            limit: 返回数量限制
            
        Returns:
            List[CandidateEvaluation]: 评价列表
        """
        service = self._get_service()
        repo = self._evaluation_repo
        
        if repo is None:
            from ..infrastructure.database import DatabaseCandidateEvaluationRepository
            repo = DatabaseCandidateEvaluationRepository()
        
        return await repo.list_by_job(job_id, limit)
    
    async def get_candidate_evaluations(
        self,
        candidate_id: str,
        limit: int = 50
    ) -> List[CandidateEvaluation]:
        """
        获取候选人的所有评价
        
        Args:
            candidate_id: 候选人ID
            limit: 返回数量限制
            
        Returns:
            List[CandidateEvaluation]: 评价列表
        """
        repo = self._evaluation_repo
        
        if repo is None:
            from ..infrastructure.database import DatabaseCandidateEvaluationRepository
            repo = DatabaseCandidateEvaluationRepository()
        
        return await repo.list_by_candidate(candidate_id, limit)
    
    async def generate_report(self, evaluation_id: str) -> Optional[CandidateEvaluationReport]:
        """
        生成评价报告
        
        Args:
            evaluation_id: 评价ID
            
        Returns:
            Optional[CandidateEvaluationReport]: 评价报告
        """
        service = self._get_service()
        return await service.generate_report(evaluation_id)
