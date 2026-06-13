"""
候选人评价模型

基于"双Agent协同评价模型"：
1. 初筛Agent：基于量化人岗匹配模型，完成简历结构化提取、硬性条件过滤、语义匹配打分
2. 深度评估Agent：基于冰山模型+STAR框架，生成面试题并做软素质量化评分
3. 最终汇总：整合初筛得分+深度评估得分，输出完整评价报告
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class EvaluationStage(Enum):
    """评价阶段"""
    INITIAL_SCREENING = "initial_screening"  # 初筛阶段
    DEEP_ASSESSMENT = "deep_assessment"      # 深度评估阶段
    FINAL_REPORT = "final_report"            # 最终报告阶段


class IcebergDimension(Enum):
    """冰山模型维度"""
    KNOWLEDGE = "knowledge"                  # 知识
    SKILLS = "skills"                        # 技能
    SELF_KNOWLEDGE = "self_knowledge"        # 自我认知
    TRAITS = "traits"                        # 特质
    MOTIVES = "motives"                      # 动机
    VALUES = "values"                        # 价值观


class StarDimension(Enum):
    """STAR面试法维度"""
    SITUATION = "situation"                  # 情境
    TASK = "task"                            # 任务
    ACTION = "action"                        # 行动
    RESULT = "result"                         # 结果


@dataclass
class StructuredResume:
    """
    结构化简历数据
    
    从原始简历中提取的标准化结构化信息。
    """
    candidate_id: str
    
    # 基本信息
    name: str = ""
    age: Optional[int] = None
    gender: str = ""
    location: str = ""
    contact: Dict[str, str] = field(default_factory=dict)
    
    # 教育背景
    education: List[Dict[str, Any]] = field(default_factory=list)
    highest_degree: str = ""
    graduate_school: str = ""
    major: str = ""
    
    # 工作经历
    work_experience: List[Dict[str, Any]] = field(default_factory=list)
    total_years: float = 0.0
    current_company: str = ""
    current_position: str = ""
    
    # 技能
    hard_skills: List[str] = field(default_factory=list)
    soft_skills: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    
    # 项目经历
    projects: List[Dict[str, Any]] = field(default_factory=list)
    
    # 原始文本
    raw_resume_text: str = ""
    extraction_confidence: float = 0.0  # 提取置信度 0-1


@dataclass
class HardConditionFilter:
    """
    硬性条件过滤结果
    
    检验候选人是否满足岗位的基本要求。
    """
    job_id: str
    candidate_id: str
    
    # 硬性条件检查
    education_met: bool = True
    education_detail: str = ""
    
    experience_met: bool = True
    experience_detail: str = ""
    
    skills_met: bool = True
    skills_detail: str = ""
    
    certification_met: bool = True
    certification_detail: str = ""
    
    location_met: bool = True
    location_detail: str = ""
    
    salary_met: bool = True
    salary_detail: str = ""
    
    # 综合结果
    all_conditions_met: bool = True
    failed_conditions: List[str] = field(default_factory=list)
    pass_score: float = 0.0  # 通过程度 0-100


@dataclass
class SemanticMatchResult:
    """
    语义匹配结果
    
    基于NLP技术的人岗语义匹配评分。
    """
    job_id: str
    candidate_id: str
    
    # 匹配维度
    title_match_score: float = 0.0     # 岗位 title 匹配度 0-100
    skill_match_score: float = 0.0     # 技能匹配度 0-100
    experience_match_score: float = 0.0  # 经验匹配度 0-100
    industry_match_score: float = 0.0  # 行业匹配度 0-100
    culture_match_score: float = 0.0    # 文化匹配度 0-100
    
    # 综合评分
    overall_similarity: float = 0.0    # 综合相似度 0-100
    rank: int = 0                       # 排名
    percentile: float = 0.0            # 百分位
    
    # 匹配分析
    matching_skills: List[str] = field(default_factory=list)    # 匹配的技能
    missing_skills: List[str] = field(default_factory=list)      # 缺失的技能
    highlight_experiences: List[str] = field(default_factory=list)  # 亮点经历


@dataclass
class InitialScreeningResult:
    """
    初筛Agent结果
    
    整合结构化简历、硬性条件过滤和语义匹配的结果。
    """
    candidate_id: str
    job_id: str
    
    # 阶段信息
    evaluation_id: str
    evaluation_stage: EvaluationStage = EvaluationStage.INITIAL_SCREENING
    
    # 结构化简历
    structured_resume: Optional[StructuredResume] = None
    
    # 硬性条件过滤
    hard_condition_filter: Optional[HardConditionFilter] = None
    
    # 语义匹配
    semantic_match: Optional[SemanticMatchResult] = None
    
    # 综合初筛评分
    screening_score: float = 0.0  # 综合初筛得分 0-100
    screening_passed: bool = True
    screening_rank: int = 0
    
    # 建议
    recommendations: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)
    
    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class SoftQualityDimension:
    """
    软素质维度评分
    
    基于冰山模型评估候选人的软素质。
    """
    dimension: IcebergDimension
    score: float                      # 0-100
    evidence: List[str] = field(default_factory=list)  # 评分依据
    examples: List[str] = field(default_factory=list)  # 具体案例
    confidence: float = 0.0           # 评估置信度 0-1


@dataclass
class StarResponse:
    """
    STAR面试回答
    
    结构化的行为面试回答。
    """
    dimension: StarDimension
    question: str                     # 原始问题
    situation: str = ""               # 情境描述
    task: str = ""                    # 任务描述
    action: str = ""                  # 行动描述
    result: str = ""                  # 结果描述
    
    # 评分
    content_score: float = 0.0       # 内容评分 0-100
    structure_score: float = 0.0      # 结构评分 0-100
    overall_score: float = 0.0        # 综合评分 0-100
    
    # 分析
    key_behaviors: List[str] = field(default_factory=list)
    red_flags: List[str] = field(default_factory=list)


@dataclass
class InterviewQuestion:
    """
    面试问题
    
    针对特定软素质维度生成的面试问题。
    """
    question_id: str
    dimension: IcebergDimension
    question_text: str
    question_type: str  # "behavioral", "situational", "hypothetical"
    follow_up_questions: List[str] = field(default_factory=list)
    expected_keywords: List[str] = field(default_factory=list)
    difficulty_level: str = "medium"  # "easy", "medium", "hard"


@dataclass
class DeepAssessmentResult:
    """
    深度评估Agent结果
    
    基于冰山模型和STAR框架的深度软素质评估。
    """
    candidate_id: str
    job_id: str
    
    # 阶段信息
    evaluation_id: str
    evaluation_stage: EvaluationStage = EvaluationStage.DEEP_ASSESSMENT
    
    # 面试问题
    interview_questions: List[InterviewQuestion] = field(default_factory=list)
    
    # 软素质评分
    soft_quality_scores: List[SoftQualityDimension] = field(default_factory=list)
    
    # STAR回答
    star_responses: List[StarResponse] = field(default_factory=list)
    
    # 综合软素质评分
    overall_soft_score: float = 0.0  # 综合软素质得分 0-100
    
    # 文化匹配度
    culture_fit_score: float = 0.0   # 文化匹配度 0-100
    growth_potential_score: float = 0.0  # 成长潜力 0-100
    
    # 综合深度评估评分
    assessment_score: float = 0.0    # 综合评估得分 0-100
    
    # 洞察
    key_strengths: List[str] = field(default_factory=list)
    development_areas: List[str] = field(default_factory=list)
    risk_indicators: List[str] = field(default_factory=list)
    
    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    assessment_duration_minutes: int = 0


@dataclass
class CandidateEvaluation:
    """
    候选人综合评价
    
    整合初筛Agent和深度评估Agent的结果，提供完整的候选人评价。
    """
    candidate_id: str
    job_id: str
    evaluation_id: str
    
    # 初筛结果
    initial_screening: Optional[InitialScreeningResult] = None
    
    # 深度评估结果
    deep_assessment: Optional[DeepAssessmentResult] = None
    
    # 评价阶段
    current_stage: EvaluationStage = EvaluationStage.INITIAL_SCREENING
    
    # 综合评分
    initial_screening_weight: float = 0.4   # 初筛权重
    deep_assessment_weight: float = 0.6     # 深度评估权重
    
    final_score: float = 0.0                # 最终综合得分 0-100
    percentile: float = 0.0                 # 百分位排名
    
    # 评价等级
    evaluation_level: str = ""              # "A": 强烈推荐, "B": 推荐, "C": 待定, "D": 不推荐
    evaluation_summary: str = ""
    
    # 决策建议
    recommendation: str = ""                 # "strong_buy", "buy", "hold", "reject"
    decision_reasons: List[str] = field(default_factory=list)
    
    # 评价信息
    evaluation_date: datetime = field(default_factory=datetime.now)
    evaluator_version: str = "1.0"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_complete(self) -> bool:
        """检查评价是否完成"""
        return (self.initial_screening is not None and 
                self.deep_assessment is not None)
    
    def get_score_breakdown(self) -> Dict[str, float]:
        """获取评分明细"""
        breakdown = {}
        if self.initial_screening:
            breakdown["initial_screening"] = self.initial_screening.screening_score
        if self.deep_assessment:
            breakdown["soft_quality"] = self.deep_assessment.overall_soft_score
            breakdown["culture_fit"] = self.deep_assessment.culture_fit_score
            breakdown["growth_potential"] = self.deep_assessment.growth_potential_score
        breakdown["final_score"] = self.final_score
        return breakdown


@dataclass
class CandidateEvaluationReport:
    """
    候选人评价报告
    
    面向企业的结构化评价报告，包含完整的评估详情和决策支持。
    """
    candidate_evaluation: CandidateEvaluation
    
    # 执行摘要
    executive_summary: str = ""
    
    # 亮点总结
    highlights: List[str] = field(default_factory=list)
    
    # 关注点
    concerns: List[str] = field(default_factory=list)
    
    # 人岗匹配分析
    job_fit_analysis: Dict[str, Any] = field(default_factory=dict)
    
    # 风险评估
    risk_assessment: Dict[str, float] = field(default_factory=dict)
    
    # 对比分析（可选）
    comparison_with_other_candidates: List[Dict[str, Any]] = field(default_factory=list)
    
    # 生成时间
    generated_at: datetime = field(default_factory=datetime.now)
    
    def get_recommendation_display(self) -> str:
        """获取推荐等级的显示文本"""
        mapping = {
            "strong_buy": "强烈推荐",
            "buy": "推荐",
            "hold": "待定",
            "reject": "不推荐"
        }
        return mapping.get(self.candidate_evaluation.recommendation, "未知")
