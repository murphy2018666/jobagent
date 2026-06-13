"""
评价模块API路由

提供企业评价和候选人评价的RESTful接口。
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..application.services import get_company_repo, get_candidate_repo, get_job_repo
from ..infrastructure.enterprise_evaluator import EnterpriseEvaluationService
from ..infrastructure.candidate_evaluator import CandidateEvaluationService


# ============== 请求/响应模型 ==============

# 企业评价请求
class EnterpriseEvaluationRequest(BaseModel):
    """企业评价请求"""
    company_id: str = Field(..., description="企业ID")
    company_data: Dict[str, Any] = Field(default_factory=dict, description="企业基本信息和发展数据")
    financial_data: Optional[Dict[str, Any]] = Field(None, description="财务数据")
    industry_data: Optional[Dict[str, Any]] = Field(None, description="行业数据")


class EnterpriseEvaluationResponse(BaseModel):
    """企业评价响应"""
    evaluation_id: str
    company_id: str
    overall_score: float
    competitiveness_level: str
    seven_s_overall_score: float
    cash_flow_score: float
    dupont_score: float
    porter_score: float
    strengths: List[str]
    weaknesses: List[str]
    evaluation_date: datetime


# 候选人评价请求
class CandidateEvaluationRequest(BaseModel):
    """候选人评价请求"""
    candidate_id: str = Field(..., description="候选人ID")
    job_id: str = Field(..., description="岗位ID")
    perform_deep_assessment: bool = Field(True, description="是否执行深度评估")


class CandidateEvaluationResponse(BaseModel):
    """候选人评价响应"""
    evaluation_id: str
    candidate_id: str
    job_id: str
    current_stage: str
    initial_screening_score: float
    deep_assessment_score: Optional[float] = None
    final_score: float
    evaluation_level: str
    recommendation: str
    evaluation_date: datetime


class InitialScreeningResponse(BaseModel):
    """初筛结果响应"""
    evaluation_id: str
    candidate_id: str
    job_id: str
    screening_score: float
    screening_passed: bool
    hard_conditions_met: bool
    hard_condition_details: Dict[str, Any]
    semantic_match_score: float
    matching_skills: List[str]
    missing_skills: List[str]
    recommendations: List[str]
    concerns: List[str]


class DeepAssessmentResponse(BaseModel):
    """深度评估响应"""
    evaluation_id: str
    candidate_id: str
    job_id: str
    overall_soft_score: float
    culture_fit_score: float
    growth_potential_score: float
    assessment_score: float
    soft_quality_dimensions: List[Dict[str, Any]]
    interview_questions: List[Dict[str, Any]]
    key_strengths: List[str]
    development_areas: List[str]
    risk_indicators: List[str]


# 报告响应
class EvaluationReportResponse(BaseModel):
    """评价报告响应"""
    evaluation_id: str
    report_type: str  # "enterprise" or "candidate"
    summary: str
    key_metrics: Dict[str, Any]
    risk_alerts: List[Dict[str, Any]]
    recommendations: List[Any]
    generated_at: datetime


# ============== 路由定义 ==============

router = APIRouter(prefix="/api/v1/evaluations", tags=["评价模块"])


# ============== 企业评价接口 ==============

@router.post("/enterprise", response_model=EnterpriseEvaluationResponse)
async def create_enterprise_evaluation(
    request: EnterpriseEvaluationRequest,
    company_repo=Depends(get_company_repo)
):
    """
    创建企业评价
    
    对企业进行综合评价，基于麦肯锡7S模型、Dickinson现金流模型、杜邦分析和波特五力模型。
    
    Args:
        request: 企业评价请求
        
    Returns:
        EnterpriseEvaluationResponse: 企业评价结果
    """
    from ..application.services import EnterpriseEvaluationApplicationService
    
    # 创建应用服务
    service = EnterpriseEvaluationApplicationService(company_repo)
    
    try:
        evaluation = await service.evaluate_company(
            company_id=request.company_id,
            company_data=request.company_data,
            financial_data=request.financial_data,
            industry_data=request.industry_data
        )
        
        return EnterpriseEvaluationResponse(
            evaluation_id=evaluation.evaluation_id,
            company_id=evaluation.company_id,
            overall_score=evaluation.overall_score,
            competitiveness_level=evaluation.competitiveness_level,
            seven_s_overall_score=evaluation.seven_s_overall_score,
            cash_flow_score=evaluation.cash_flow_score,
            dupont_score=evaluation.dupont_score,
            porter_score=evaluation.porter_score,
            strengths=evaluation.strengths,
            weaknesses=evaluation.weaknesses,
            evaluation_date=evaluation.evaluation_date
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"企业评价失败: {str(e)}"
        )


@router.get("/enterprise/{company_id}", response_model=List[EnterpriseEvaluationResponse])
async def get_company_evaluations(
    company_id: str,
    limit: int = 10
):
    """
    获取企业的评价历史
    
    Args:
        company_id: 企业ID
        limit: 返回数量限制
        
    Returns:
        List[EnterpriseEvaluationResponse]: 评价历史列表
    """
    from ..application.services import EnterpriseEvaluationApplicationService
    
    try:
        service = EnterpriseEvaluationApplicationService(None)
        evaluations = await service.get_evaluation_history(company_id, limit)
        
        return [
            EnterpriseEvaluationResponse(
                evaluation_id=ev.evaluation_id,
                company_id=ev.company_id,
                overall_score=ev.overall_score,
                competitiveness_level=ev.competitiveness_level,
                seven_s_overall_score=ev.seven_s_overall_score,
                cash_flow_score=ev.cash_flow_score,
                dupont_score=ev.dupont_score,
                porter_score=ev.porter_score,
                strengths=ev.strengths,
                weaknesses=ev.weaknesses,
                evaluation_date=ev.evaluation_date
            )
            for ev in evaluations
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取评价历史失败: {str(e)}"
        )


@router.get("/enterprise/latest/{company_id}", response_model=EnterpriseEvaluationResponse)
async def get_latest_enterprise_evaluation(company_id: str):
    """
    获取企业最新评价
    
    Args:
        company_id: 企业ID
        
    Returns:
        EnterpriseEvaluationResponse: 最新评价
    """
    from ..application.services import EnterpriseEvaluationApplicationService
    
    try:
        service = EnterpriseEvaluationApplicationService(None)
        evaluation = await service.get_latest_evaluation(company_id)
        
        if not evaluation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到企业评价"
            )
        
        return EnterpriseEvaluationResponse(
            evaluation_id=evaluation.evaluation_id,
            company_id=evaluation.company_id,
            overall_score=evaluation.overall_score,
            competitiveness_level=evaluation.competitiveness_level,
            seven_s_overall_score=evaluation.seven_s_overall_score,
            cash_flow_score=evaluation.cash_flow_score,
            dupont_score=evaluation.dupont_score,
            porter_score=evaluation.porter_score,
            strengths=evaluation.strengths,
            weaknesses=evaluation.weaknesses,
            evaluation_date=evaluation.evaluation_date
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取最新评价失败: {str(e)}"
        )


# ============== 候选人评价接口 ==============

@router.post("/candidate", response_model=CandidateEvaluationResponse)
async def create_candidate_evaluation(
    request: CandidateEvaluationRequest,
    candidate_repo=Depends(get_candidate_repo),
    job_repo=Depends(get_job_repo)
):
    """
    创建候选人评价
    
    对候选人进行综合评价，采用双Agent协同评价模型：
    1. 初筛Agent：基于量化人岗匹配模型
    2. 深度评估Agent：基于冰山模型+STAR框架
    
    Args:
        request: 候选人评价请求
        
    Returns:
        CandidateEvaluationResponse: 候选人评价结果
    """
    from ..application.services import CandidateEvaluationApplicationService
    
    # 创建应用服务
    service = CandidateEvaluationApplicationService(
        candidate_repo, job_repo
    )
    
    try:
        evaluation = await service.evaluate_candidate(
            candidate_id=request.candidate_id,
            job_id=request.job_id,
            perform_deep_assessment=request.perform_deep_assessment
        )
        
        return CandidateEvaluationResponse(
            evaluation_id=evaluation.evaluation_id,
            candidate_id=evaluation.candidate_id,
            job_id=evaluation.job_id,
            current_stage=evaluation.current_stage.value,
            initial_screening_score=evaluation.initial_screening.screening_score if evaluation.initial_screening else 0,
            deep_assessment_score=evaluation.deep_assessment.assessment_score if evaluation.deep_assessment else None,
            final_score=evaluation.final_score,
            evaluation_level=evaluation.evaluation_level,
            recommendation=evaluation.recommendation,
            evaluation_date=evaluation.evaluation_date
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"候选人评价失败: {str(e)}"
        )


@router.get("/candidate/{evaluation_id}", response_model=CandidateEvaluationResponse)
async def get_candidate_evaluation(evaluation_id: str):
    """
    获取候选人评价详情
    
    Args:
        evaluation_id: 评价ID
        
    Returns:
        CandidateEvaluationResponse: 评价详情
    """
    from ..application.services import CandidateEvaluationApplicationService
    
    try:
        service = CandidateEvaluationApplicationService(None, None)
        evaluation = await service.get_evaluation(evaluation_id)
        
        if not evaluation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到评价"
            )
        
        return CandidateEvaluationResponse(
            evaluation_id=evaluation.evaluation_id,
            candidate_id=evaluation.candidate_id,
            job_id=evaluation.job_id,
            current_stage=evaluation.current_stage.value,
            initial_screening_score=evaluation.initial_screening.screening_score if evaluation.initial_screening else 0,
            deep_assessment_score=evaluation.deep_assessment.assessment_score if evaluation.deep_assessment else None,
            final_score=evaluation.final_score,
            evaluation_level=evaluation.evaluation_level,
            recommendation=evaluation.recommendation,
            evaluation_date=evaluation.evaluation_date
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取评价失败: {str(e)}"
        )


@router.get("/candidate/initial/{evaluation_id}", response_model=InitialScreeningResponse)
async def get_initial_screening_result(evaluation_id: str):
    """
    获取初筛结果
    
    Args:
        evaluation_id: 评价ID
        
    Returns:
        InitialScreeningResponse: 初筛结果
    """
    from ..application.services import CandidateEvaluationApplicationService
    
    try:
        service = CandidateEvaluationApplicationService(None, None)
        evaluation = await service.get_evaluation(evaluation_id)
        
        if not evaluation or not evaluation.initial_screening:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到初筛结果"
            )
        
        screening = evaluation.initial_screening
        hard_filter = screening.hard_condition_filter
        
        return InitialScreeningResponse(
            evaluation_id=evaluation.evaluation_id,
            candidate_id=screening.candidate_id,
            job_id=screening.job_id,
            screening_score=screening.screening_score,
            screening_passed=screening.screening_passed,
            hard_conditions_met=hard_filter.all_conditions_met if hard_filter else True,
            hard_condition_details={
                "education_met": hard_filter.education_met if hard_filter else True,
                "experience_met": hard_filter.experience_met if hard_filter else True,
                "skills_met": hard_filter.skills_met if hard_filter else True,
                "failed_conditions": hard_filter.failed_conditions if hard_filter else []
            },
            semantic_match_score=screening.semantic_match.overall_similarity if screening.semantic_match else 0,
            matching_skills=screening.semantic_match.matching_skills if screening.semantic_match else [],
            missing_skills=screening.semantic_match.missing_skills if screening.semantic_match else [],
            recommendations=screening.recommendations,
            concerns=screening.concerns
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取初筛结果失败: {str(e)}"
        )


@router.get("/candidate/deep/{evaluation_id}", response_model=DeepAssessmentResponse)
async def get_deep_assessment_result(evaluation_id: str):
    """
    获取深度评估结果
    
    Args:
        evaluation_id: 评价ID
        
    Returns:
        DeepAssessmentResponse: 深度评估结果
    """
    from ..application.services import CandidateEvaluationApplicationService
    
    try:
        service = CandidateEvaluationApplicationService(None, None)
        evaluation = await service.get_evaluation(evaluation_id)
        
        if not evaluation or not evaluation.deep_assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到深度评估结果"
            )
        
        assessment = evaluation.deep_assessment
        
        return DeepAssessmentResponse(
            evaluation_id=evaluation.evaluation_id,
            candidate_id=assessment.candidate_id,
            job_id=assessment.job_id,
            overall_soft_score=assessment.overall_soft_score,
            culture_fit_score=assessment.culture_fit_score,
            growth_potential_score=assessment.growth_potential_score,
            assessment_score=assessment.assessment_score,
            soft_quality_dimensions=[
                {
                    "dimension": sq.dimension.value,
                    "score": sq.score,
                    "evidence": sq.evidence,
                    "confidence": sq.confidence
                }
                for sq in assessment.soft_quality_scores
            ],
            interview_questions=[
                {
                    "question_id": q.question_id,
                    "dimension": q.dimension.value,
                    "question_text": q.question_text,
                    "question_type": q.question_type
                }
                for q in assessment.interview_questions
            ],
            key_strengths=assessment.key_strengths,
            development_areas=assessment.development_areas,
            risk_indicators=assessment.risk_indicators
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取深度评估结果失败: {str(e)}"
        )


@router.get("/candidate/job/{job_id}/evaluations", response_model=List[CandidateEvaluationResponse])
async def get_job_candidate_evaluations(
    job_id: str,
    limit: int = 100
):
    """
    获取岗位的所有候选人评价
    
    Args:
        job_id: 岗位ID
        limit: 返回数量限制
        
    Returns:
        List[CandidateEvaluationResponse]: 评价列表
    """
    from ..application.services import CandidateEvaluationApplicationService
    
    try:
        service = CandidateEvaluationApplicationService(None, None)
        evaluations = await service.get_job_evaluations(job_id, limit)
        
        return [
            CandidateEvaluationResponse(
                evaluation_id=ev.evaluation_id,
                candidate_id=ev.candidate_id,
                job_id=ev.job_id,
                current_stage=ev.current_stage.value,
                initial_screening_score=ev.initial_screening.screening_score if ev.initial_screening else 0,
                deep_assessment_score=ev.deep_assessment.assessment_score if ev.deep_assessment else None,
                final_score=ev.final_score,
                evaluation_level=ev.evaluation_level,
                recommendation=ev.recommendation,
                evaluation_date=ev.evaluation_date
            )
            for ev in evaluations
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取评价列表失败: {str(e)}"
        )


# ============== 报告接口 ==============

@router.get("/enterprise/report/{evaluation_id}", response_model=EvaluationReportResponse)
async def get_enterprise_evaluation_report(evaluation_id: str):
    """
    获取企业评价报告
    
    Args:
        evaluation_id: 评价ID
        
    Returns:
        EvaluationReportResponse: 评价报告
    """
    from ..application.services import EnterpriseEvaluationApplicationService
    
    try:
        service = EnterpriseEvaluationApplicationService(None)
        report = await service.generate_report(evaluation_id)
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到评价报告"
            )
        
        return EvaluationReportResponse(
            evaluation_id=evaluation_id,
            report_type="enterprise",
            summary=report.executive_summary,
            key_metrics=report.key_metrics,
            risk_alerts=report.risk_alerts,
            recommendations=report.improvement_priorities,
            generated_at=report.generated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取评价报告失败: {str(e)}"
        )


@router.get("/candidate/report/{evaluation_id}", response_model=EvaluationReportResponse)
async def get_candidate_evaluation_report(evaluation_id: str):
    """
    获取候选人评价报告
    
    Args:
        evaluation_id: 评价ID
        
    Returns:
        EvaluationReportResponse: 评价报告
    """
    from ..application.services import CandidateEvaluationApplicationService
    
    try:
        service = CandidateEvaluationApplicationService(None, None)
        report = await service.generate_report(evaluation_id)
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到评价报告"
            )
        
        return EvaluationReportResponse(
            evaluation_id=evaluation_id,
            report_type="candidate",
            summary=report.executive_summary,
            key_metrics={
                "final_score": report.candidate_evaluation.final_score,
                "initial_screening_score": report.candidate_evaluation.initial_screening.screening_score if report.candidate_evaluation.initial_screening else 0,
                "deep_assessment_score": report.candidate_evaluation.deep_assessment.assessment_score if report.candidate_evaluation.deep_assessment else 0
            },
            risk_alerts=[
                {"type": "risk", "message": r}
                for r in report.concerns
            ],
            recommendations=report.highlights,
            generated_at=report.generated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取评价报告失败: {str(e)}"
        )
