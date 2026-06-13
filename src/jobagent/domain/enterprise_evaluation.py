"""
企业评价模型

基于麦肯锡7S模型、Dickinson现金流模型、杜邦分析模型和波特五力模型，
提供企业整体综合竞争力诊断、生命周期划分、财务盈利质量拆解和行业竞争地位评价。
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class LifeCycleStage(Enum):
    """企业发展生命周期阶段"""
    INTRODUCTION = "introduction"      # 导入期
    GROWTH = "growth"                  # 成长期
    MATURE = "mature"                  # 成熟期
    DECLINE = "decline"                # 衰退期
    UNKNOWN = "unknown"                 # 未知


class SevenSDimension(Enum):
    """麦肯锡7S模型维度"""
    STRATEGY = "strategy"              # 战略
    STRUCTURE = "structure"            # 结构
    SYSTEMS = "systems"                # 制度
    SHARED_VALUES = "shared_values"    # 共同价值观
    STYLE = "style"                    # 风格
    STAFF = "staff"                    # 员工
    SKILLS = "skills"                  # 技能


@dataclass
class SevenSEvaluation:
    """7S模型评价结果"""
    dimension: SevenSDimension
    score: float                      # 0-100分
    weight: float                    # 权重
    description: str                  # 评价描述
    suggestions: List[str] = field(default_factory=list)  # 改进建议


@dataclass
class CashFlowAnalysis:
    """Dickinson现金流模型分析"""
    operating_cash_flow: float        # 经营性现金流
    investing_cash_flow: float        # 投资性现金流
    financing_cash_flow: float        # 融资性现金流
    life_cycle_stage: LifeCycleStage  # 生命周期阶段
    cash_flow_pattern: str            # 现金流模式描述
    stability_score: float           # 稳定性评分 0-100


@dataclass
class DuPontAnalysis:
    """杜邦财务分析"""
    roe: float                        # 净资产收益率
    net_profit_margin: float          # 净利率
    asset_turnover: float             # 资产周转率
    financial_leverage: float         # 财务杠杆
    gross_margin: float               # 毛利率
    operating_margin: float          # 营业利润率
    debt_ratio: float                 # 资产负债率
    current_ratio: float              # 流动比率
    quick_ratio: float                # 速动比率
    profitability_score: float        # 盈利能力评分 0-100
    operating_efficiency_score: float # 经营效率评分 0-100
    financial_health_score: float     # 财务健康评分 0-100


@dataclass
class PorterAnalysis:
    """波特五力分析"""
    threat_of_new_entrants: float     # 新进入者威胁 0-100
    bargaining_power_of_suppliers: float  # 供应商议价能力 0-100
    bargaining_power_of_buyers: float    # 购买者议价能力 0-100
    threat_of_substitutes: float      # 替代品威胁 0-100
    industry_rivalry: float           # 行业内竞争 0-100
    competitive_advantage_score: float    # 竞争优势评分 0-100
    moat_type: str                    # 护城河类型
    moat_strength: str                # 护城河强度


@dataclass
class EnterpriseEvaluation:
    """
    企业综合评价
    
    整合7S模型、Dickinson现金流模型、杜邦分析和波特五力模型，
    提供企业整体竞争力的多维度评估。
    """
    company_id: str
    evaluation_id: str
    
    # 7S综合评价
    seven_s_scores: List[SevenSEvaluation] = field(default_factory=list)
    seven_s_overall_score: float = 0.0  # 7S综合得分 0-100
    
    # 现金流分析
    cash_flow_analysis: Optional[CashFlowAnalysis] = None
    cash_flow_score: float = 0.0        # 现金流评分 0-100
    
    # 杜邦分析
    dupont_analysis: Optional[DuPontAnalysis] = None
    dupont_score: float = 0.0          # 杜邦评分 0-100
    
    # 波特五力分析
    porter_analysis: Optional[PorterAnalysis] = None
    porter_score: float = 0.0          # 波特评分 0-100
    
    # 综合评价
    overall_score: float = 0.0         # 综合竞争力得分 0-100
    competitiveness_level: str = ""    # 竞争力等级：优秀/良好/一般/较弱
    strengths: List[str] = field(default_factory=list)    # 优势
    weaknesses: List[str] = field(default_factory=list)  # 劣势
    opportunities: List[str] = field(default_factory=list)   # 机会
    threats: List[str] = field(default_factory=list)    # 威胁
    
    # 评价信息
    evaluation_date: datetime = field(default_factory=datetime.now)
    valid_until: datetime = field(default=None)
    evaluator_version: str = "1.0"
    raw_data: Dict[str, Any] = field(default_factory=dict)  # 原始评价数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_dimension_score(self, dimension: SevenSDimension) -> Optional[float]:
        """获取指定维度的评分"""
        for score in self.seven_s_scores:
            if score.dimension == dimension:
                return score.score
        return None
    
    def get_swot_summary(self) -> Dict[str, List[str]]:
        """获取SWOT分析摘要"""
        return {
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "opportunities": self.opportunities,
            "threats": self.threats
        }
    
    def is_expired(self) -> bool:
        """检查评价是否过期"""
        if self.valid_until is None:
            return False
        return datetime.now() > self.valid_until


@dataclass
class EvaluationReport:
    """
    企业评价报告
    
    面向用户的结构化评价报告，包含可视化和决策支持信息。
    """
    enterprise_evaluation: EnterpriseEvaluation
    
    # 执行摘要
    executive_summary: str = ""
    
    # 关键指标
    key_metrics: Dict[str, float] = field(default_factory=dict)
    
    # 行业对标
    industry_benchmark: Dict[str, float] = field(default_factory=dict)
    
    # 发展趋势
    trend_analysis: Dict[str, List[float]] = field(default_factory=dict)
    
    # 风险提示
    risk_alerts: List[Dict[str, str]] = field(default_factory=list)
    
    # 改进建议优先级
    improvement_priorities: List[Dict[str, Any]] = field(default_factory=list)
    
    # 生成时间
    generated_at: datetime = field(default_factory=datetime.now)
    
    def get_top_strengths(self, n: int = 3) -> List[str]:
        """获取最重要的N个优势"""
        return self.enterprise_evaluation.strengths[:n]
    
    def get_top_weaknesses(self, n: int = 3) -> List[str]:
        """获取最重要的N个劣势"""
        return self.enterprise_evaluation.weaknesses[:n]
