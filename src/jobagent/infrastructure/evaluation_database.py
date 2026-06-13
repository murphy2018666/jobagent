"""
评价模块数据库仓储实现

提供企业评价和候选人评价的持久化实现。
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import json

from sqlalchemy import Column, String, Text, DateTime, Float, JSON, ForeignKey, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship

from ..domain.evaluation_repositories import (
    EnterpriseEvaluationRepository,
    CandidateEvaluationRepository
)
from ..domain.enterprise_evaluation import (
    EnterpriseEvaluation, EvaluationReport,
    SevenSDimension, SevenSEvaluation,
    CashFlowAnalysis, LifeCycleStage,
    DuPontAnalysis, PorterAnalysis
)
from ..domain.candidate_evaluation import (
    CandidateEvaluation, CandidateEvaluationReport,
    InitialScreeningResult, DeepAssessmentResult,
    StructuredResume, HardConditionFilter, SemanticMatchResult,
    SoftQualityDimension, StarResponse, InterviewQuestion,
    IcebergDimension, StarDimension, EvaluationStage
)
from .database import Base, get_session


class DBEnterpriseEvaluation(Base):
    """企业评价数据库模型"""
    __tablename__ = "enterprise_evaluations"
    
    id = Column(String(36), primary_key=True)
    company_id = Column(String(36), nullable=False, index=True)
    
    # 7S评价数据
    seven_s_data = Column(JSON)
    seven_s_overall_score = Column(Float, default=0.0)
    
    # 现金流数据
    cash_flow_data = Column(JSON)
    cash_flow_score = Column(Float, default=0.0)
    
    # 杜邦分析数据
    dupont_data = Column(JSON)
    dupont_score = Column(Float, default=0.0)
    
    # 波特五力数据
    porter_data = Column(JSON)
    porter_score = Column(Float, default=0.0)
    
    # 综合评价
    overall_score = Column(Float, default=0.0)
    competitiveness_level = Column(String(20))
    
    # SWOT分析
    strengths = Column(JSON)
    weaknesses = Column(JSON)
    opportunities = Column(JSON)
    threats = Column(JSON)
    
    # 元数据
    evaluation_date = Column(DateTime, default=datetime.now)
    valid_until = Column(DateTime, nullable=True)
    evaluator_version = Column(String(10), default="1.0")
    raw_data = Column(JSON)
    metadata = Column(JSON)


class DBCandidateEvaluation(Base):
    """候选人评价数据库模型"""
    __tablename__ = "candidate_evaluations"
    
    id = Column(String(36), primary_key=True)
    candidate_id = Column(String(36), nullable=False, index=True)
    job_id = Column(String(36), nullable=False, index=True)
    
    # 评价阶段
    current_stage = Column(String(30), default="initial_screening")
    
    # 权重配置
    initial_screening_weight = Column(Float, default=0.4)
    deep_assessment_weight = Column(Float, default=0.6)
    
    # 综合评分
    final_score = Column(Float, default=0.0)
    percentile = Column(Float, default=0.0)
    
    # 评价等级
    evaluation_level = Column(String(10))
    evaluation_summary = Column(Text)
    
    # 决策建议
    recommendation = Column(String(20))
    decision_reasons = Column(JSON)
    
    # 元数据
    evaluation_date = Column(DateTime, default=datetime.now)
    evaluator_version = Column(String(10), default="1.0")
    metadata = Column(JSON)


class DBInitialScreening(Base):
    """初筛结果数据库模型"""
    __tablename__ = "initial_screenings"
    
    id = Column(String(36), primary_key=True)
    evaluation_id = Column(String(36), ForeignKey("candidate_evaluations.id"), index=True)
    candidate_id = Column(String(36), nullable=False)
    job_id = Column(String(36), nullable=False)
    
    # 结构化简历数据
    structured_resume_data = Column(JSON)
    
    # 硬性条件过滤结果
    hard_condition_data = Column(JSON)
    
    # 语义匹配结果
    semantic_match_data = Column(JSON)
    
    # 综合评分
    screening_score = Column(Float, default=0.0)
    screening_passed = Column(String(10), default="false")
    screening_rank = Column(Integer, default=0)
    
    # 反馈
    recommendations = Column(JSON)
    concerns = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.now)


class DBDeepAssessment(Base):
    """深度评估数据库模型"""
    __tablename__ = "deep_assessments"
    
    id = Column(String(36), primary_key=True)
    evaluation_id = Column(String(36), ForeignKey("candidate_evaluations.id"), index=True)
    candidate_id = Column(String(36), nullable=False)
    job_id = Column(String(36), nullable=False)
    
    # 面试问题
    interview_questions_data = Column(JSON)
    
    # 软素质评分
    soft_quality_data = Column(JSON)
    
    # 综合软素质评分
    overall_soft_score = Column(Float, default=0.0)
    
    # 其他评分
    culture_fit_score = Column(Float, default=0.0)
    growth_potential_score = Column(Float, default=0.0)
    
    # 综合评估得分
    assessment_score = Column(Float, default=0.0)
    
    # 洞察
    key_strengths = Column(JSON)
    development_areas = Column(JSON)
    risk_indicators = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.now)
    assessment_duration_minutes = Column(Integer, default=0)


class DatabaseEnterpriseEvaluationRepository(EnterpriseEvaluationRepository):
    """
    企业评价数据库仓储实现
    """
    
    async def save(self, evaluation: EnterpriseEvaluation) -> EnterpriseEvaluation:
        """保存企业评价"""
        async for session in get_session():
            db_eval = DBEnterpriseEvaluation(
                id=evaluation.evaluation_id,
                company_id=evaluation.company_id,
                seven_s_data=json.dumps(self._serialize_seven_s(evaluation)),
                seven_s_overall_score=evaluation.seven_s_overall_score,
                cash_flow_data=json.dumps(self._serialize_cashflow(evaluation)),
                cash_flow_score=evaluation.cash_flow_score,
                dupont_data=json.dumps(self._serialize_dupont(evaluation)),
                dupont_score=evaluation.dupont_score,
                porter_data=json.dumps(self._serialize_porter(evaluation)),
                porter_score=evaluation.porter_score,
                overall_score=evaluation.overall_score,
                competitiveness_level=evaluation.competitiveness_level,
                strengths=evaluation.strengths,
                weaknesses=evaluation.weaknesses,
                opportunities=evaluation.opportunities,
                threats=evaluation.threats,
                evaluation_date=evaluation.evaluation_date,
                valid_until=evaluation.valid_until,
                raw_data=evaluation.raw_data,
                metadata=evaluation.metadata
            )
            session.add(db_eval)
            await session.commit()
            return evaluation
    
    async def get_by_id(self, evaluation_id: str) -> Optional[EnterpriseEvaluation]:
        """根据ID获取企业评价"""
        async for session in get_session():
            result = await session.execute(
                f"SELECT * FROM enterprise_evaluations WHERE id = '{evaluation_id}'"
            )
            row = result.fetchone()
            if row:
                return self._deserialize(row)
            return None
    
    async def get_latest_by_company(self, company_id: str) -> Optional[EnterpriseEvaluation]:
        """获取企业最新的评价"""
        async for session in get_session():
            result = await session.execute(
                f"SELECT * FROM enterprise_evaluations WHERE company_id = '{company_id}' "
                f"ORDER BY evaluation_date DESC LIMIT 1"
            )
            row = result.fetchone()
            if row:
                return self._deserialize(row)
            return None
    
    async def list_by_company(self, company_id: str, limit: int = 10) -> List[EnterpriseEvaluation]:
        """列出企业的评价历史"""
        evaluations = []
        async for session in get_session():
            result = await session.execute(
                f"SELECT * FROM enterprise_evaluations WHERE company_id = '{company_id}' "
                f"ORDER BY evaluation_date DESC LIMIT {limit}"
            )
            for row in result.fetchall():
                evaluations.append(self._deserialize(row))
        return evaluations
    
    async def get_report(self, evaluation_id: str) -> Optional[EvaluationReport]:
        """获取评价报告"""
        evaluation = await self.get_by_id(evaluation_id)
        if not evaluation:
            return None
        
        from ..infrastructure.enterprise_evaluator import EnterpriseEvaluationService
        service = EnterpriseEvaluationService(None, None)
        
        key_metrics = {
            "综合竞争力得分": evaluation.overall_score,
            "7S模型得分": evaluation.seven_s_overall_score,
            "现金流评分": evaluation.cash_flow_score,
            "杜邦评分": evaluation.dupont_score,
            "波特五力评分": evaluation.porter_score
        }
        
        return EvaluationReport(
            enterprise_evaluation=evaluation,
            executive_summary=f"企业综合竞争力评估得分：{evaluation.overall_score:.1f}分，{evaluation.competitiveness_level}",
            key_metrics=key_metrics
        )
    
    async def delete(self, evaluation_id: str) -> bool:
        """删除企业评价"""
        async for session in get_session():
            await session.execute(
                f"DELETE FROM enterprise_evaluations WHERE id = '{evaluation_id}'"
            )
            await session.commit()
            return True
    
    def _serialize_seven_s(self, evaluation: EnterpriseEvaluation) -> Dict:
        return {
            "scores": [
                {"dimension": s.dimension.value, "score": s.score, "weight": s.weight, 
                 "description": s.description, "suggestions": s.suggestions}
                for s in evaluation.seven_s_scores
            ]
        }
    
    def _serialize_cashflow(self, evaluation: EnterpriseEvaluation) -> Optional[Dict]:
        if not evaluation.cash_flow_analysis:
            return None
        cf = evaluation.cash_flow_analysis
        return {
            "operating_cash_flow": cf.operating_cash_flow,
            "investing_cash_flow": cf.investing_cash_flow,
            "financing_cash_flow": cf.financing_cash_flow,
            "life_cycle_stage": cf.life_cycle_stage.value,
            "cash_flow_pattern": cf.cash_flow_pattern,
            "stability_score": cf.stability_score
        }
    
    def _serialize_dupont(self, evaluation: EnterpriseEvaluation) -> Optional[Dict]:
        if not evaluation.dupont_analysis:
            return None
        d = evaluation.dupont_analysis
        return {
            "roe": d.roe,
            "net_profit_margin": d.net_profit_margin,
            "asset_turnover": d.asset_turnover,
            "financial_leverage": d.financial_leverage,
            "profitability_score": d.profitability_score,
            "operating_efficiency_score": d.operating_efficiency_score,
            "financial_health_score": d.financial_health_score
        }
    
    def _serialize_porter(self, evaluation: EnterpriseEvaluation) -> Optional[Dict]:
        if not evaluation.porter_analysis:
            return None
        p = evaluation.porter_analysis
        return {
            "threat_of_new_entrants": p.threat_of_new_entrants,
            "bargaining_power_of_suppliers": p.bargaining_power_of_suppliers,
            "bargaining_power_of_buyers": p.bargaining_power_of_buyers,
            "threat_of_substitutes": p.threat_of_substitutes,
            "industry_rivalry": p.industry_rivalry,
            "competitive_advantage_score": p.competitive_advantage_score,
            "moat_type": p.moat_type,
            "moat_strength": p.moat_strength
        }
    
    def _deserialize(self, row) -> EnterpriseEvaluation:
        """反序列化数据库行到实体"""
        seven_s_data = json.loads(row.seven_s_data) if row.seven_s_data else {"scores": []}
        seven_s_scores = []
        for s in seven_s_data.get("scores", []):
            seven_s_scores.append(SevenSEvaluation(
                dimension=SevenSDimension(s["dimension"]),
                score=s["score"],
                weight=s["weight"],
                description=s["description"],
                suggestions=s.get("suggestions", [])
            ))
        
        cash_flow_data = json.loads(row.cash_flow_data) if row.cash_flow_data else None
        cash_flow = None
        if cash_flow_data:
            cash_flow = CashFlowAnalysis(
                operating_cash_flow=cash_flow_data["operating_cash_flow"],
                investing_cash_flow=cash_flow_data["investing_cash_flow"],
                financing_cash_flow=cash_flow_data["financing_cash_flow"],
                life_cycle_stage=LifeCycleStage(cash_flow_data["life_cycle_stage"]),
                cash_flow_pattern=cash_flow_data["cash_flow_pattern"],
                stability_score=cash_flow_data["stability_score"]
            )
        
        dupont_data = json.loads(row.dupont_data) if row.dupont_data else None
        dupont = None
        if dupont_data:
            dupont = DuPontAnalysis(
                roe=dupont_data["roe"],
                net_profit_margin=dupont_data["net_profit_margin"],
                asset_turnover=dupont_data["asset_turnover"],
                financial_leverage=dupont_data["financial_leverage"],
                profitability_score=dupont_data["profitability_score"],
                operating_efficiency_score=dupont_data["operating_efficiency_score"],
                financial_health_score=dupont_data["financial_health_score"]
            )
        
        porter_data = json.loads(row.porter_data) if row.porter_data else None
        porter = None
        if porter_data:
            porter = PorterAnalysis(
                threat_of_new_entrants=porter_data["threat_of_new_entrants"],
                bargaining_power_of_suppliers=porter_data["bargaining_power_of_suppliers"],
                bargaining_power_of_buyers=porter_data["bargaining_power_of_buyers"],
                threat_of_substitutes=porter_data["threat_of_substitutes"],
                industry_rivalry=porter_data["industry_rivalry"],
                competitive_advantage_score=porter_data["competitive_advantage_score"],
                moat_type=porter_data["moat_type"],
                moat_strength=porter_data["moat_strength"]
            )
        
        return EnterpriseEvaluation(
            company_id=row.company_id,
            evaluation_id=row.id,
            seven_s_scores=seven_s_scores,
            seven_s_overall_score=row.seven_s_overall_score,
            cash_flow_analysis=cash_flow,
            cash_flow_score=row.cash_flow_score,
            dupont_analysis=dupont,
            dupont_score=row.dupont_score,
            porter_analysis=porter,
            porter_score=row.porter_score,
            overall_score=row.overall_score,
            competitiveness_level=row.competitiveness_level,
            strengths=row.strengths or [],
            weaknesses=row.weaknesses or [],
            opportunities=row.opportunities or [],
            threats=row.threats or [],
            evaluation_date=row.evaluation_date,
            valid_until=row.valid_until,
            raw_data=row.raw_data or {},
            metadata=row.metadata or {}
        )


class DatabaseCandidateEvaluationRepository(CandidateEvaluationRepository):
    """
    候选人评价数据库仓储实现
    """
    
    async def save(self, evaluation: CandidateEvaluation) -> CandidateEvaluation:
        """保存候选人评价"""
        async for session in get_session():
            db_eval = DBCandidateEvaluation(
                id=evaluation.evaluation_id,
                candidate_id=evaluation.candidate_id,
                job_id=evaluation.job_id,
                current_stage=evaluation.current_stage.value,
                initial_screening_weight=evaluation.initial_screening_weight,
                deep_assessment_weight=evaluation.deep_assessment_weight,
                final_score=evaluation.final_score,
                percentile=evaluation.percentile,
                evaluation_level=evaluation.evaluation_level,
                evaluation_summary=evaluation.evaluation_summary,
                recommendation=evaluation.recommendation,
                decision_reasons=evaluation.decision_reasons,
                evaluation_date=evaluation.evaluation_date,
                metadata=evaluation.metadata
            )
            session.add(db_eval)
            await session.commit()
            return evaluation
    
    async def get_by_id(self, evaluation_id: str) -> Optional[CandidateEvaluation]:
        """根据ID获取候选人评价"""
        async for session in get_session():
            result = await session.execute(
                f"SELECT * FROM candidate_evaluations WHERE id = '{evaluation_id}'"
            )
            row = result.fetchone()
            if row:
                return await self._deserialize(row)
            return None
    
    async def get_latest_by_candidate_job(
        self, candidate_id: str, job_id: str
    ) -> Optional[CandidateEvaluation]:
        """获取特定候选人对特定岗位的最新评价"""
        async for session in get_session():
            result = await session.execute(
                f"SELECT * FROM candidate_evaluations WHERE candidate_id = '{candidate_id}' "
                f"AND job_id = '{job_id}' ORDER BY evaluation_date DESC LIMIT 1"
            )
            row = result.fetchone()
            if row:
                return await self._deserialize(row)
            return None
    
    async def list_by_job(
        self, job_id: str, limit: int = 100
    ) -> List[CandidateEvaluation]:
        """列出岗位的所有候选人评价"""
        evaluations = []
        async for session in get_session():
            result = await session.execute(
                f"SELECT * FROM candidate_evaluations WHERE job_id = '{job_id}' "
                f"ORDER BY final_score DESC LIMIT {limit}"
            )
            for row in result.fetchall():
                evaluations.append(await self._deserialize(row))
        return evaluations
    
    async def list_by_candidate(
        self, candidate_id: str, limit: int = 50
    ) -> List[CandidateEvaluation]:
        """列出候选人的所有评价"""
        evaluations = []
        async for session in get_session():
            result = await session.execute(
                f"SELECT * FROM candidate_evaluations WHERE candidate_id = '{candidate_id}' "
                f"ORDER BY evaluation_date DESC LIMIT {limit}"
            )
            for row in result.fetchall():
                evaluations.append(await self._deserialize(row))
        return evaluations
    
    async def save_initial_screening(
        self, result: InitialScreeningResult
    ) -> InitialScreeningResult:
        """保存初筛结果"""
        async for session in get_session():
            db_screening = DBInitialScreening(
                id=str(uuid.uuid4()),
                evaluation_id=result.evaluation_id,
                candidate_id=result.candidate_id,
                job_id=result.job_id,
                structured_resume_data=self._serialize_resume(result.structured_resume),
                hard_condition_data=self._serialize_hard_filter(result.hard_condition_filter),
                semantic_match_data=self._serialize_semantic(result.semantic_match),
                screening_score=result.screening_score,
                screening_passed=str(result.screening_passed).lower(),
                screening_rank=result.screening_rank,
                recommendations=result.recommendations,
                concerns=result.concerns,
                created_at=result.created_at
            )
            session.add(db_screening)
            await session.commit()
            return result
    
    async def save_deep_assessment(
        self, result: DeepAssessmentResult
    ) -> DeepAssessmentResult:
        """保存深度评估结果"""
        async for session in get_session():
            db_assessment = DBDeepAssessment(
                id=str(uuid.uuid4()),
                evaluation_id=result.evaluation_id,
                candidate_id=result.candidate_id,
                job_id=result.job_id,
                interview_questions_data=self._serialize_questions(result.interview_questions),
                soft_quality_data=self._serialize_soft_quality(result.soft_quality_scores),
                overall_soft_score=result.overall_soft_score,
                culture_fit_score=result.culture_fit_score,
                growth_potential_score=result.growth_potential_score,
                assessment_score=result.assessment_score,
                key_strengths=result.key_strengths,
                development_areas=result.development_areas,
                risk_indicators=result.risk_indicators,
                created_at=result.created_at,
                assessment_duration_minutes=result.assessment_duration_minutes
            )
            session.add(db_assessment)
            await session.commit()
            return result
    
    async def get_report(self, evaluation_id: str) -> Optional[CandidateEvaluationReport]:
        """获取评价报告"""
        evaluation = await self.get_by_id(evaluation_id)
        if not evaluation:
            return None
        
        return CandidateEvaluationReport(
            candidate_evaluation=evaluation,
            executive_summary=evaluation.evaluation_summary or "",
            highlights=[],
            concerns=evaluation.decision_reasons or []
        )
    
    async def delete(self, evaluation_id: str) -> bool:
        """删除候选人评价"""
        async for session in get_session():
            await session.execute(
                f"DELETE FROM candidate_evaluations WHERE id = '{evaluation_id}'"
            )
            await session.commit()
            return True
    
    def _serialize_resume(self, resume) -> Optional[Dict]:
        if not resume:
            return None
        return {
            "name": resume.name,
            "age": resume.age,
            "highest_degree": resume.highest_degree,
            "major": resume.major,
            "total_years": resume.total_years,
            "hard_skills": resume.hard_skills,
            "soft_skills": resume.soft_skills,
            "certifications": resume.certifications
        }
    
    def _serialize_hard_filter(self, filter_result) -> Optional[Dict]:
        if not filter_result:
            return None
        return {
            "all_conditions_met": filter_result.all_conditions_met,
            "failed_conditions": filter_result.failed_conditions,
            "pass_score": filter_result.pass_score,
            "education_met": filter_result.education_met,
            "experience_met": filter_result.experience_met,
            "skills_met": filter_result.skills_met
        }
    
    def _serialize_semantic(self, semantic) -> Optional[Dict]:
        if not semantic:
            return None
        return {
            "overall_similarity": semantic.overall_similarity,
            "skill_match_score": semantic.skill_match_score,
            "experience_match_score": semantic.experience_match_score,
            "matching_skills": semantic.matching_skills,
            "missing_skills": semantic.missing_skills
        }
    
    def _serialize_questions(self, questions) -> List[Dict]:
        return [
            {
                "question_id": q.question_id,
                "dimension": q.dimension.value,
                "question_text": q.question_text,
                "question_type": q.question_type
            }
            for q in questions
        ]
    
    def _serialize_soft_quality(self, scores) -> List[Dict]:
        return [
            {
                "dimension": sq.dimension.value,
                "score": sq.score,
                "evidence": sq.evidence,
                "confidence": sq.confidence
            }
            for sq in scores
        ]
    
    async def _deserialize(self, row) -> CandidateEvaluation:
        """反序列化数据库行到实体"""
        # 获取初筛结果
        initial_screening = None
        async for session in get_session():
            result = await session.execute(
                f"SELECT * FROM initial_screenings WHERE evaluation_id = '{row.id}' LIMIT 1"
            )
            screening_row = result.fetchone()
            if screening_row:
                initial_screening = self._deserialize_screening(screening_row)
        
        # 获取深度评估
        deep_assessment = None
        async for session in get_session():
            result = await session.execute(
                f"SELECT * FROM deep_assessments WHERE evaluation_id = '{row.id}' LIMIT 1"
            )
            assessment_row = result.fetchone()
            if assessment_row:
                deep_assessment = self._deserialize_assessment(assessment_row)
        
        return CandidateEvaluation(
            candidate_id=row.candidate_id,
            job_id=row.job_id,
            evaluation_id=row.id,
            initial_screening=initial_screening,
            deep_assessment=deep_assessment,
            current_stage=EvaluationStage(row.current_stage),
            initial_screening_weight=row.initial_screening_weight,
            deep_assessment_weight=row.deep_assessment_weight,
            final_score=row.final_score,
            percentile=row.percentile,
            evaluation_level=row.evaluation_level,
            evaluation_summary=row.evaluation_summary,
            recommendation=row.recommendation,
            decision_reasons=row.decision_reasons or [],
            evaluation_date=row.evaluation_date,
            metadata=row.metadata or {}
        )
    
    def _deserialize_screening(self, row) -> InitialScreeningResult:
        resume_data = json.loads(row.structured_resume_data) if row.structured_resume_data else None
        resume = None
        if resume_data:
            resume = StructuredResume(
                candidate_id=row.candidate_id,
                name=resume_data.get("name", ""),
                age=resume_data.get("age"),
                highest_degree=resume_data.get("highest_degree", ""),
                major=resume_data.get("major", ""),
                total_years=resume_data.get("total_years", 0),
                hard_skills=resume_data.get("hard_skills", []),
                soft_skills=resume_data.get("soft_skills", []),
                certifications=resume_data.get("certifications", [])
            )
        
        hard_data = json.loads(row.hard_condition_data) if row.hard_condition_data else None
        hard_filter = None
        if hard_data:
            hard_filter = HardConditionFilter(
                job_id=row.job_id,
                candidate_id=row.candidate_id,
                all_conditions_met=hard_data.get("all_conditions_met", False),
                failed_conditions=hard_data.get("failed_conditions", []),
                pass_score=hard_data.get("pass_score", 0)
            )
        
        semantic_data = json.loads(row.semantic_match_data) if row.semantic_match_data else None
        semantic = None
        if semantic_data:
            semantic = SemanticMatchResult(
                job_id=row.job_id,
                candidate_id=row.candidate_id,
                overall_similarity=semantic_data.get("overall_similarity", 0),
                skill_match_score=semantic_data.get("skill_match_score", 0),
                experience_match_score=semantic_data.get("experience_match_score", 0),
                matching_skills=semantic_data.get("matching_skills", []),
                missing_skills=semantic_data.get("missing_skills", [])
            )
        
        return InitialScreeningResult(
            candidate_id=row.candidate_id,
            job_id=row.job_id,
            evaluation_id=row.evaluation_id,
            structured_resume=resume,
            hard_condition_filter=hard_filter,
            semantic_match=semantic,
            screening_score=row.screening_score,
            screening_passed=row.screening_passed == "true",
            screening_rank=row.screening_rank,
            recommendations=row.recommendations or [],
            concerns=row.concerns or [],
            created_at=row.created_at
        )
    
    def _deserialize_assessment(self, row) -> DeepAssessmentResult:
        soft_data = json.loads(row.soft_quality_data) if row.soft_quality_data else []
        soft_scores = [
            SoftQualityDimension(
                dimension=IcebergDimension(s["dimension"]),
                score=s["score"],
                evidence=s.get("evidence", []),
                confidence=s.get("confidence", 0.5)
            )
            for s in soft_data
        ]
        
        return DeepAssessmentResult(
            candidate_id=row.candidate_id,
            job_id=row.job_id,
            evaluation_id=row.evaluation_id,
            interview_questions=[],
            soft_quality_scores=soft_scores,
            overall_soft_score=row.overall_soft_score,
            culture_fit_score=row.culture_fit_score,
            growth_potential_score=row.growth_potential_score,
            assessment_score=row.assessment_score,
            key_strengths=row.key_strengths or [],
            development_areas=row.development_areas or [],
            risk_indicators=row.risk_indicators or [],
            created_at=row.created_at,
            assessment_duration_minutes=row.assessment_duration_minutes
        )
