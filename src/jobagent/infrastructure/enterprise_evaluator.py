"""
企业评价服务实现

实现基于麦肯锡7S模型、Dickinson现金流模型、杜邦分析模型和波特五力模型的企业综合评价。
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
import re
from loguru import logger

from ..domain.enterprise_evaluation import (
    EnterpriseEvaluation, EvaluationReport,
    SevenSDimension, SevenSEvaluation,
    CashFlowAnalysis, LifeCycleStage,
    DuPontAnalysis,
    PorterAnalysis
)
from ..domain.repositories import CompanyRepository
from ..domain.evaluation_repositories import EnterpriseEvaluationRepository


class SevenSAnalyzer:
    """
    麦肯锡7S模型分析器
    
    评估企业在战略、结构、制度、共同价值观、风格、员工和技能七个维度的竞争力。
    """
    
    # 各维度权重
    DIMENSION_WEIGHTS = {
        SevenSDimension.STRATEGY: 0.20,
        SevenSDimension.STRUCTURE: 0.12,
        SevenSDimension.SYSTEMS: 0.12,
        SevenSDimension.SHARED_VALUES: 0.18,
        SevenSDimension.STYLE: 0.10,
        SevenSDimension.STAFF: 0.14,
        SevenSDimension.SKILLS: 0.14,
    }
    
    def analyze(self, company_data: Dict[str, Any]) -> tuple[List[SevenSEvaluation], float]:
        """
        执行7S分析
        
        Args:
            company_data: 企业数据
            
        Returns:
            Tuple[List[SevenSEvaluation], float]: 评价列表和综合得分
        """
        scores = []
        total_weighted_score = 0.0
        
        # 战略分析
        strategy_score = self._analyze_strategy(company_data)
        strategy_eval = SevenSEvaluation(
            dimension=SevenSDimension.STRATEGY,
            score=strategy_score,
            weight=self.DIMENSION_WEIGHTS[SevenSDimension.STRATEGY],
            description=self._describe_strategy(strategy_score),
            suggestions=self._suggest_strategy_improvements(company_data)
        )
        scores.append(strategy_eval)
        total_weighted_score += strategy_score * strategy_eval.weight
        
        # 结构分析
        structure_score = self._analyze_structure(company_data)
        structure_eval = SevenSEvaluation(
            dimension=SevenSDimension.STRUCTURE,
            score=structure_score,
            weight=self.DIMENSION_WEIGHTS[SevenSDimension.STRUCTURE],
            description=self._describe_structure(structure_score),
            suggestions=self._suggest_structure_improvements(company_data)
        )
        scores.append(structure_eval)
        total_weighted_score += structure_score * structure_eval.weight
        
        # 制度分析
        systems_score = self._analyze_systems(company_data)
        systems_eval = SevenSEvaluation(
            dimension=SevenSDimension.SYSTEMS,
            score=systems_score,
            weight=self.DIMENSION_WEIGHTS[SevenSDimension.SYSTEMS],
            description=self._describe_systems(systems_score),
            suggestions=self._suggest_systems_improvements(company_data)
        )
        scores.append(systems_eval)
        total_weighted_score += systems_score * systems_eval.weight
        
        # 共同价值观分析
        values_score = self._analyze_shared_values(company_data)
        values_eval = SevenSEvaluation(
            dimension=SevenSDimension.SHARED_VALUES,
            score=values_score,
            weight=self.DIMENSION_WEIGHTS[SevenSDimension.SHARED_VALUES],
            description=self._describe_shared_values(values_score),
            suggestions=self._suggest_values_improvements(company_data)
        )
        scores.append(values_eval)
        total_weighted_score += values_score * values_eval.weight
        
        # 风格分析
        style_score = self._analyze_style(company_data)
        style_eval = SevenSEvaluation(
            dimension=SevenSDimension.STYLE,
            score=style_score,
            weight=self.DIMENSION_WEIGHTS[SevenSDimension.STYLE],
            description=self._describe_style(style_score),
            suggestions=self._suggest_style_improvements(company_data)
        )
        scores.append(style_eval)
        total_weighted_score += style_score * style_eval.weight
        
        # 员工分析
        staff_score = self._analyze_staff(company_data)
        staff_eval = SevenSEvaluation(
            dimension=SevenSDimension.STAFF,
            score=staff_score,
            weight=self.DIMENSION_WEIGHTS[SevenSDimension.STAFF],
            description=self._describe_staff(staff_score),
            suggestions=self._suggest_staff_improvements(company_data)
        )
        scores.append(staff_eval)
        total_weighted_score += staff_score * staff_eval.weight
        
        # 技能分析
        skills_score = self._analyze_skills(company_data)
        skills_eval = SevenSEvaluation(
            dimension=SevenSDimension.SKILLS,
            score=skills_score,
            weight=self.DIMENSION_WEIGHTS[SevenSDimension.SKILLS],
            description=self._describe_skills(skills_score),
            suggestions=self._suggest_skills_improvements(company_data)
        )
        scores.append(skills_eval)
        total_weighted_score += skills_score * skills_eval.weight
        
        return scores, total_weighted_score
    
    def _analyze_strategy(self, data: Dict) -> float:
        """分析战略维度"""
        # 基于企业描述、愿景使命、市场定位等信息评分
        score = 50.0
        if data.get("vision"):
            score += 10
        if data.get("mission"):
            score += 10
        if data.get("competitive_advantage"):
            score += 15
        if data.get("market_position"):
            score += 10
        if data.get("long_term_plan"):
            score += 5
        return min(score, 100.0)
    
    def _analyze_structure(self, data: Dict) -> float:
        """分析结构维度"""
        score = 50.0
        if data.get("org_structure"):
            score += 15
        if data.get("reporting_lines"):
            score += 15
        if data.get("department_coordination"):
            score += 10
        if data.get("decision_efficiency"):
            score += 10
        return min(score, 100.0)
    
    def _analyze_systems(self, data: Dict) -> float:
        """分析制度维度"""
        score = 50.0
        if data.get("management_systems"):
            score += 15
        if data.get("process_standardization"):
            score += 15
        if data.get("information_systems"):
            score += 10
        if data.get("performance_management"):
            score += 10
        return min(score, 100.0)
    
    def _analyze_shared_values(self, data: Dict) -> float:
        """分析共同价值观维度"""
        score = 50.0
        if data.get("corporate_culture"):
            score += 15
        if data.get("core_values"):
            score += 15
        if data.get("employee_beliefs"):
            score += 10
        if data.get("ethical_standards"):
            score += 10
        return min(score, 100.0)
    
    def _analyze_style(self, data: Dict) -> float:
        """分析风格维度"""
        score = 50.0
        if data.get("leadership_style"):
            score += 15
        if data.get("management_approach"):
            score += 15
        if data.get("organizational_atmosphere"):
            score += 10
        if data.get("innovation_culture"):
            score += 10
        return min(score, 100.0)
    
    def _analyze_staff(self, data: Dict) -> float:
        """分析员工维度"""
        score = 50.0
        if data.get("employee_quality"):
            score += 15
        if data.get("talent_development"):
            score += 15
        if data.get("team_stability"):
            score += 10
        if data.get("motivation_system"):
            score += 10
        return min(score, 100.0)
    
    def _analyze_skills(self, data: Dict) -> float:
        """分析技能维度"""
        score = 50.0
        if data.get("core_competencies"):
            score += 15
        if data.get("technical_capabilities"):
            score += 15
        if data.get("innovation_capability"):
            score += 10
        if data.get("learning_ability"):
            score += 10
        return min(score, 100.0)
    
    def _describe_strategy(self, score: float) -> str:
        if score >= 80: return "战略清晰，具有明确的竞争优势"
        elif score >= 60: return "战略较为明确，需强化差异化"
        elif score >= 40: return "战略模糊，需要明确市场定位"
        else: return "缺乏清晰战略"
    
    def _describe_structure(self, score: float) -> str:
        if score >= 80: return "组织结构合理，决策高效"
        elif score >= 60: return "组织结构合理，沟通需改进"
        elif score >= 40: return "组织结构需要优化"
        else: return "组织结构混乱"
    
    def _describe_systems(self, score: float) -> str:
        if score >= 80: return "制度完善，执行力强"
        elif score >= 60: return "制度较为完善，需强化落实"
        elif score >= 40: return "制度体系不健全"
        else: return "缺乏规范化制度"
    
    def _describe_shared_values(self, score: float) -> str:
        if score >= 80: return "价值观统一，文化认同度高"
        elif score >= 60: return "文化氛围良好，需强化认同"
        elif score >= 40: return "文化需要塑造"
        else: return "缺乏统一价值观"
    
    def _describe_style(self, score: float) -> str:
        if score >= 80: return "领导风格开明，创新氛围浓厚"
        elif score >= 60: return "领导风格稳健，氛围较好"
        elif score >= 40: return "管理风格保守"
        else: return "缺乏管理风格"
    
    def _describe_staff(self, score: float) -> str:
        if score >= 80: return "人才储备充足，团队稳定"
        elif score >= 60: return "人才结构合理，稳定性一般"
        elif score >= 40: return "人才结构需要优化"
        else: return "人才流失严重"
    
    def _describe_skills(self, score: float) -> str:
        if score >= 80: return "核心能力突出，学习能力强"
        elif score >= 60: return "技能储备良好，需持续提升"
        elif score >= 40: return "技能水平需要提升"
        else: return "核心能力不足"
    
    def _suggest_strategy_improvements(self, data: Dict) -> List[str]:
        suggestions = []
        if not data.get("vision"): suggestions.append("明确企业愿景")
        if not data.get("competitive_advantage"): suggestions.append("识别和强化竞争优势")
        if not data.get("long_term_plan"): suggestions.append("制定长期发展规划")
        return suggestions
    
    def _suggest_structure_improvements(self, data: Dict) -> List[str]:
        suggestions = []
        if not data.get("org_structure"): suggestions.append("优化组织架构")
        if not data.get("decision_efficiency"): suggestions.append("提高决策效率")
        return suggestions
    
    def _suggest_systems_improvements(self, data: Dict) -> List[str]:
        suggestions = []
        if not data.get("management_systems"): suggestions.append("完善管理制度")
        if not data.get("process_standardization"): suggestions.append("推进流程标准化")
        return suggestions
    
    def _suggest_values_improvements(self, data: Dict) -> List[str]:
        suggestions = []
        if not data.get("core_values"): suggestions.append("塑造核心价值观")
        if not data.get("corporate_culture"): suggestions.append("建设企业文化")
        return suggestions
    
    def _suggest_style_improvements(self, data: Dict) -> List[str]:
        suggestions = []
        if not data.get("innovation_culture"): suggestions.append("鼓励创新文化")
        if not data.get("leadership_style"): suggestions.append("完善领导力发展")
        return suggestions
    
    def _suggest_staff_improvements(self, data: Dict) -> List[str]:
        suggestions = []
        if not data.get("talent_development"): suggestions.append("加强人才培养")
        if not data.get("motivation_system"): suggestions.append("优化激励机制")
        return suggestions
    
    def _suggest_skills_improvements(self, data: Dict) -> List[str]:
        suggestions = []
        if not data.get("core_competencies"): suggestions.append("培育核心能力")
        if not data.get("innovation_capability"): suggestions.append("提升创新能力")
        return suggestions


class DickinsonCashFlowAnalyzer:
    """
    Dickinson现金流模型分析器
    
    基于经营、投资、融资三类现金流组合，客观划分企业发展生命周期。
    """
    
    def analyze(
        self,
        operating_cash_flow: float,
        investing_cash_flow: float,
        financing_cash_flow: float,
        additional_data: Dict[str, Any] = None
    ) -> CashFlowAnalysis:
        """
        执行现金流分析
        
        基于现金流模式判断企业所处生命周期阶段。
        
        Args:
            operating_cash_flow: 经营性现金流
            investing_cash_flow: 投资性现金流
            financing_cash_flow: 融资性现金流
            additional_data: 额外财务数据
            
        Returns:
            CashFlowAnalysis: 现金流分析结果
        """
        # 确定现金流模式
        cash_flow_pattern, life_cycle_stage = self._determine_lifecycle(
            operating_cash_flow,
            investing_cash_flow,
            financing_cash_flow
        )
        
        # 计算稳定性评分
        stability_score = self._calculate_stability(
            operating_cash_flow,
            investing_cash_flow,
            financing_cash_flow
        )
        
        return CashFlowAnalysis(
            operating_cash_flow=operating_cash_flow,
            investing_cash_flow=investing_cash_flow,
            financing_cash_flow=financing_cash_flow,
            life_cycle_stage=life_cycle_stage,
            cash_flow_pattern=cash_flow_pattern,
            stability_score=stability_score
        )
    
    def _determine_lifecycle(
        self,
        operating: float,
        investing: float,
        financing: float
    ) -> tuple[str, LifeCycleStage]:
        """根据现金流组合判断生命周期"""
        patterns = {
            (">0", "<0", ">0"): ("导入期-扩张型", LifeCycleStage.INTRODUCTION),
            (">0", "<0", "<0"): ("导入期-稳健型", LifeCycleStage.INTRODUCTION),
            (">0", "<0", "<0"): ("成长期", LifeCycleStage.GROWTH),
            (">0", "<0", "<0"): ("成熟期", LifeCycleStage.MATURE),
            ("<0", "<0", ">0"): ("成熟期-转型型", LifeCycleStage.MATURE),
            ("<0", ">0", ">0"): ("衰退期-挣扎型", LifeCycleStage.DECLINE),
            ("<0", ">0", "<0"): ("衰退期-收缩型", LifeCycleStage.DECLINE),
        }
        
        op_sign = ">0" if operating >= 0 else "<0"
        inv_sign = ">0" if investing >= 0 else "<0"
        fin_sign = ">0" if financing >= 0 else "<0"
        
        pattern_key = (op_sign, inv_sign, fin_sign)
        
        if pattern_key in patterns:
            return patterns[pattern_key]
        
        return ("模式不明确", LifeCycleStage.UNKNOWN)
    
    def _calculate_stability(
        self,
        operating: float,
        investing: float,
        financing: float
    ) -> float:
        """计算现金流稳定性评分"""
        score = 50.0
        
        # 经营性现金流为正加分
        if operating > 0:
            score += 20
        elif operating < 0:
            score -= 20
        
        # 投资性现金流合理性
        if -abs(operating * 0.5) <= investing <= -abs(operating * 0.1):
            score += 15
        
        # 融资性现金流与业务匹配度
        if (operating > 0 and financing < 0) or (operating < 0 and financing > 0):
            score += 15
        
        return max(0.0, min(100.0, score))


class DuPontAnalyzer:
    """
    杜邦财务分析器
    
    通过拆解ROE分析企业的盈利能力、经营效率和财务杠杆。
    """
    
    def analyze(
        self,
        financial_data: Dict[str, Any]
    ) -> DuPontAnalysis:
        """
        执行杜邦分析
        
        Args:
            financial_data: 财务数据字典
            
        Returns:
            DuPontAnalysis: 杜邦分析结果
        """
        # 提取财务指标
        revenue = financial_data.get("revenue", 0)
        net_profit = financial_data.get("net_profit", 0)
        total_assets = financial_data.get("total_assets", 1)
        equity = financial_data.get("equity", 1)
        cogs = financial_data.get("cogs", 0)
        operating_profit = financial_data.get("operating_profit", 0)
        current_liabilities = financial_data.get("current_liabilities", 0)
        current_assets = financial_data.get("current_assets", 0)
        inventory = financial_data.get("inventory", 0)
        
        # 计算杜邦指标
        net_profit_margin = (net_profit / revenue * 100) if revenue else 0
        asset_turnover = (revenue / total_assets) if total_assets else 0
        financial_leverage = (total_assets / equity) if equity else 0
        roe = net_profit_margin * asset_turnover * financial_leverage
        
        gross_margin = ((revenue - cogs) / revenue * 100) if revenue else 0
        operating_margin = (operating_profit / revenue * 100) if revenue else 0
        
        debt_ratio = ((total_assets - equity) / total_assets * 100) if total_assets else 0
        current_ratio = (current_assets / current_liabilities) if current_liabilities else 0
        quick_ratio = ((current_assets - inventory) / current_liabilities) if current_liabilities else 0
        
        # 计算维度评分
        profitability_score = self._score_profitability(net_profit_margin, gross_margin, operating_margin)
        operating_efficiency_score = self._score_operating_efficiency(asset_turnover, revenue, total_assets)
        financial_health_score = self._score_financial_health(debt_ratio, current_ratio, quick_ratio)
        
        return DuPontAnalysis(
            roe=roe,
            net_profit_margin=net_profit_margin,
            asset_turnover=asset_turnover,
            financial_leverage=financial_leverage,
            gross_margin=gross_margin,
            operating_margin=operating_margin,
            debt_ratio=debt_ratio,
            current_ratio=current_ratio,
            quick_ratio=quick_ratio,
            profitability_score=profitability_score,
            operating_efficiency_score=operating_efficiency_score,
            financial_health_score=financial_health_score
        )
    
    def _score_profitability(self, net_margin: float, gross_margin: float, op_margin: float) -> float:
        """评分盈利能力"""
        score = 30.0
        
        # 净利率评分
        if net_margin >= 15: score += 25
        elif net_margin >= 10: score += 20
        elif net_margin >= 5: score += 15
        elif net_margin >= 0: score += 10
        else: score -= 10
        
        # 毛利率评分
        if gross_margin >= 40: score += 25
        elif gross_margin >= 25: score += 20
        elif gross_margin >= 15: score += 15
        else: score += 10
        
        # 营业利润率评分
        if op_margin >= 20: score += 20
        elif op_margin >= 10: score += 15
        elif op_margin >= 5: score += 10
        else: score += 5
        
        return max(0.0, min(100.0, score))
    
    def _score_operating_efficiency(self, turnover: float, revenue: float, assets: float) -> float:
        """评分经营效率"""
        score = 30.0
        
        # 资产周转率评分
        if turnover >= 2.0: score += 30
        elif turnover >= 1.5: score += 25
        elif turnover >= 1.0: score += 20
        elif turnover >= 0.5: score += 15
        else: score += 10
        
        # 绝对值评分
        if revenue >= 10000000: score += 20
        elif revenue >= 1000000: score += 15
        elif revenue >= 100000: score += 10
        
        if assets >= 5000000: score += 20
        elif assets >= 500000: score += 15
        elif assets >= 50000: score += 10
        
        return max(0.0, min(100.0, score))
    
    def _score_financial_health(self, debt_ratio: float, current_ratio: float, quick_ratio: float) -> float:
        """评分财务健康"""
        score = 30.0
        
        # 资产负债率评分
        if debt_ratio <= 30: score += 25
        elif debt_ratio <= 50: score += 20
        elif debt_ratio <= 70: score += 15
        else: score += 5
        
        # 流动比率评分
        if current_ratio >= 2.0: score += 25
        elif current_ratio >= 1.5: score += 20
        elif current_ratio >= 1.0: score += 15
        else: score += 5
        
        # 速动比率评分
        if quick_ratio >= 1.0: score += 20
        elif quick_ratio >= 0.8: score += 15
        elif quick_ratio >= 0.5: score += 10
        else: score += 5
        
        return max(0.0, min(100.0, score))


class PorterAnalyzer:
    """
    波特五力分析器
    
    评估行业竞争地位和企业的护城河。
    """
    
    def analyze(
        self,
        industry_data: Dict[str, Any],
        company_data: Dict[str, Any]
    ) -> PorterAnalysis:
        """
        执行波特五力分析
        
        Args:
            industry_data: 行业数据
            company_data: 企业数据
            
        Returns:
            PorterAnalysis: 波特五力分析结果
        """
        # 五力评分
        threat_of_new_entrants = self._analyze_new_entrant_threat(industry_data, company_data)
        supplier_power = self._analyze_supplier_power(industry_data, company_data)
        buyer_power = self._analyze_buyer_power(industry_data, company_data)
        substitute_threat = self._analyze_substitute_threat(industry_data, company_data)
        rivalry = self._analyze_industry_rivalry(industry_data, company_data)
        
        # 计算竞争优势评分
        competitive_score = self._calculate_competitive_score(
            threat_of_new_entrants,
            supplier_power,
            buyer_power,
            substitute_threat,
            rivalry
        )
        
        # 判断护城河
        moat_type, moat_strength = self._analyze_moat(company_data)
        
        return PorterAnalysis(
            threat_of_new_entrants=threat_of_new_entrants,
            bargaining_power_of_suppliers=supplier_power,
            bargaining_power_of_buyers=buyer_power,
            threat_of_substitutes=substitute_threat,
            industry_rivalry=rivalry,
            competitive_advantage_score=competitive_score,
            moat_type=moat_type,
            moat_strength=moat_strength
        )
    
    def _analyze_new_entrant_threat(self, industry: Dict, company: Dict) -> float:
        """分析新进入者威胁"""
        score = 50.0
        
        # 行业壁垒
        barriers = industry.get("entry_barriers", "medium")
        if barriers == "high": score -= 20
        elif barriers == "medium": score += 0
        else: score += 20
        
        # 规模经济
        if industry.get("economies_of_scale", False): score -= 10
        if industry.get("capital_requirements", "medium") == "high": score -= 10
        
        # 品牌忠诚度
        if company.get("brand_loyalty", "medium") == "high": score -= 10
        elif company.get("brand_loyalty", "medium") == "low": score += 10
        
        return max(0.0, min(100.0, score))
    
    def _analyze_supplier_power(self, industry: Dict, company: Dict) -> float:
        """分析供应商议价能力"""
        score = 50.0
        
        if industry.get("supplier_concentration", "medium") == "high": score += 15
        elif industry.get("supplier_concentration", "medium") == "low": score -= 15
        
        if industry.get("supplier_switching_cost", "medium") == "high": score += 15
        if industry.get("forward_integration", False): score -= 15
        
        return max(0.0, min(100.0, score))
    
    def _analyze_buyer_power(self, industry: Dict, company: Dict) -> float:
        """分析购买者议价能力"""
        score = 50.0
        
        if industry.get("buyer_concentration", "medium") == "high": score += 15
        if industry.get("buyer_switching_cost", "medium") == "low": score += 15
        
        if company.get("differentiation", "medium") == "high": score -= 15
        
        return max(0.0, min(100.0, score))
    
    def _analyze_substitute_threat(self, industry: Dict, company: Dict) -> float:
        """分析替代品威胁"""
        score = 50.0
        
        if industry.get("substitute_availability", "medium") == "high": score += 20
        if industry.get("substitute_price_performance", "medium") == "high": score += 15
        
        if company.get("innovation_ability", "medium") == "high": score -= 15
        
        return max(0.0, min(100.0, score))
    
    def _analyze_industry_rivalry(self, industry: Dict, company: Dict) -> float:
        """分析行业内竞争"""
        score = 50.0
        
        if industry.get("competitor_count", "medium") == "many": score += 15
        elif industry.get("competitor_count", "medium") == "few": score -= 15
        
        if industry.get("industry_growth", "medium") == "slow": score += 15
        elif industry.get("industry_growth", "medium") == "fast": score -= 15
        
        if company.get("market_share", 0) >= 30: score -= 10
        
        return max(0.0, min(100.0, score))
    
    def _calculate_competitive_score(
        self,
        new_entrant: float,
        supplier: float,
        buyer: float,
        substitute: float,
        rivalry: float
    ) -> float:
        """计算竞争优势评分"""
        # 新进入者威胁高是劣势，转换为竞争优势
        new_entrant_adv = 100 - new_entrant
        # 供应商能力强是劣势
        supplier_adv = 100 - supplier
        # 购买者能力强是劣势
        buyer_adv = 100 - buyer
        # 替代品威胁高是劣势
        substitute_adv = 100 - substitute
        # 竞争激烈是劣势
        rivalry_adv = 100 - rivalry
        
        return (new_entrant_adv * 0.2 + 
                supplier_adv * 0.15 + 
                buyer_adv * 0.15 + 
                substitute_adv * 0.2 + 
                rivalry_adv * 0.3)
    
    def _analyze_moat(self, company: Dict) -> tuple[str, str]:
        """分析护城河类型和强度"""
        moats = []
        
        if company.get("brand_value"):
            moats.append("品牌护城河")
        if company.get("patents"):
            moats.append("专利护城河")
        if company.get("network_effect"):
            moats.append("网络效应护城河")
        if company.get("cost_advantage"):
            moats.append("成本护城河")
        if company.get("switching_cost"):
            moats.append("转换成本护城河")
        
        if not moats:
            return "无明显护城河", "较弱"
        
        strength = "强" if len(moats) >= 3 else "中等" if len(moats) >= 2 else "一般"
        
        return "、".join(moats), strength


class EnterpriseEvaluationService:
    """
    企业评价服务
    
    整合7S模型、Dickinson现金流模型、杜邦分析和波特五力模型，
    提供企业整体竞争力的多维度评估。
    """
    
    def __init__(
        self,
        company_repo: CompanyRepository,
        evaluation_repo: EnterpriseEvaluationRepository
    ):
        """
        初始化企业评价服务
        
        Args:
            company_repo: 企业仓储实例
            evaluation_repo: 企业评价仓储实例
        """
        self.company_repo = company_repo
        self.evaluation_repo = evaluation_repo
        self.seven_s_analyzer = SevenSAnalyzer()
        self.cashflow_analyzer = DickinsonCashFlowAnalyzer()
        self.dupont_analyzer = DuPontAnalyzer()
        self.porter_analyzer = PorterAnalyzer()
    
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
        evaluation_id = str(uuid.uuid4())
        
        # 7S模型分析
        seven_s_scores, seven_s_overall = self.seven_s_analyzer.analyze(company_data)
        
        # 现金流分析（如果有财务数据）
        cashflow_analysis = None
        cashflow_score = 0.0
        if financial_data:
            cashflow_analysis = self.cashflow_analyzer.analyze(
                operating_cash_flow=financial_data.get("operating_cash_flow", 0),
                investing_cash_flow=financial_data.get("investing_cash_flow", 0),
                financing_cash_flow=financial_data.get("financing_cash_flow", 0),
                additional_data=financial_data
            )
            cashflow_score = cashflow_analysis.stability_score
        
        # 杜邦分析（如果有财务数据）
        dupont_analysis = None
        dupont_score = 0.0
        if financial_data:
            dupont_analysis = self.dupont_analyzer.analyze(financial_data)
            dupont_score = (
                dupont_analysis.profitability_score * 0.4 +
                dupont_analysis.operating_efficiency_score * 0.3 +
                dupont_analysis.financial_health_score * 0.3
            )
        
        # 波特五力分析（如果有行业数据）
        porter_analysis = None
        porter_score = 0.0
        if industry_data:
            porter_analysis = self.porter_analyzer.analyze(industry_data, company_data)
            porter_score = porter_analysis.competitive_advantage_score
        
        # 计算综合得分
        overall_score = self._calculate_overall_score(
            seven_s_overall,
            cashflow_score,
            dupont_score,
            porter_score,
            has_financial_data=financial_data is not None,
            has_industry_data=industry_data is not None
        )
        
        # 确定竞争力等级
        competitiveness_level = self._determine_competitiveness_level(overall_score)
        
        # SWOT分析
        strengths, weaknesses, opportunities, threats = self._perform_swot_analysis(
            seven_s_scores,
            cashflow_analysis,
            dupont_analysis,
            porter_analysis
        )
        
        # 构建评价实体
        evaluation = EnterpriseEvaluation(
            company_id=company_id,
            evaluation_id=evaluation_id,
            seven_s_scores=seven_s_scores,
            seven_s_overall_score=seven_s_overall,
            cash_flow_analysis=cashflow_analysis,
            cash_flow_score=cashflow_score,
            dupont_analysis=dupont_analysis,
            dupont_score=dupont_score,
            porter_analysis=porter_analysis,
            porter_score=porter_score,
            overall_score=overall_score,
            competitiveness_level=competitiveness_level,
            strengths=strengths,
            weaknesses=weaknesses,
            opportunities=opportunities,
            threats=threats,
            raw_data={
                "company_data": company_data,
                "financial_data": financial_data,
                "industry_data": industry_data
            }
        )
        
        # 保存评价
        await self.evaluation_repo.save(evaluation)
        
        return evaluation
    
    def _calculate_overall_score(
        self,
        seven_s_score: float,
        cashflow_score: float,
        dupont_score: float,
        porter_score: float,
        has_financial_data: bool,
        has_industry_data: bool
    ) -> float:
        """计算综合得分"""
        weights = {
            "seven_s": 0.30,
            "cashflow": 0.20 if has_financial_data else 0,
            "dupont": 0.25 if has_financial_data else 0,
            "porter": 0.25 if has_industry_data else 0
        }
        
        # 归一化权重
        total_weight = sum(w for w in weights.values())
        if total_weight == 0:
            return seven_s_score
        
        weighted_sum = (
            seven_s_score * weights["seven_s"] +
            cashflow_score * weights["cashflow"] +
            dupont_score * weights["dupont"] +
            porter_score * weights["porter"]
        )
        
        return weighted_sum / total_weight
    
    def _determine_competitiveness_level(self, score: float) -> str:
        """确定竞争力等级"""
        if score >= 80:
            return "优秀"
        elif score >= 65:
            return "良好"
        elif score >= 50:
            return "一般"
        else:
            return "较弱"
    
    def _perform_swot_analysis(
        self,
        seven_s_scores: List[SevenSEvaluation],
        cashflow: Optional[CashFlowAnalysis],
        dupont: Optional[DuPontAnalysis],
        porter: Optional[PorterAnalysis]
    ) -> tuple[List[str], List[str], List[str], List[str]]:
        """执行SWOT分析"""
        strengths = []
        weaknesses = []
        opportunities = []
        threats = []
        
        # 从7S分析提取
        for score in seven_s_scores:
            if score.score >= 70:
                strengths.append(f"{score.dimension.value}能力突出")
            elif score.score < 50:
                weaknesses.append(f"{score.dimension.value}需要改进")
        
        # 从现金流分析提取
        if cashflow:
            if cashflow.stability_score >= 70:
                strengths.append("现金流稳定")
            elif cashflow.stability_score < 50:
                weaknesses.append("现金流不稳定")
            
            if cashflow.life_cycle_stage.value in ["growth"]:
                opportunities.append("处于成长期，发展潜力大")
            elif cashflow.life_cycle_stage.value in ["decline"]:
                threats.append("处于衰退期，需转型升级")
        
        # 从杜邦分析提取
        if dupont:
            if dupont.profitability_score >= 70:
                strengths.append("盈利能力良好")
            if dupont.financial_health_score < 50:
                weaknesses.append("财务风险较高")
        
        # 从波特分析提取
        if porter:
            if porter.competitive_advantage_score >= 70:
                strengths.append("竞争优势明显")
                strengths.append(f"护城河：{porter.moat_type}")
            if porter.threat_of_new_entrants >= 70:
                threats.append("新进入者威胁大")
            if porter.industry_rivalry >= 70:
                threats.append("行业竞争激烈")
        
        return strengths[:5], weaknesses[:5], opportunities[:5], threats[:5]
    
    async def get_latest_evaluation(self, company_id: str) -> Optional[EnterpriseEvaluation]:
        """
        获取企业最新评价
        
        Args:
            company_id: 企业ID
            
        Returns:
            Optional[EnterpriseEvaluation]: 最新评价
        """
        return await self.evaluation_repo.get_latest_by_company(company_id)
    
    async def generate_report(self, evaluation_id: str) -> Optional[EvaluationReport]:
        """
        生成评价报告
        
        Args:
            evaluation_id: 评价ID
            
        Returns:
            Optional[EvaluationReport]: 评价报告
        """
        evaluation = await self.evaluation_repo.get_by_id(evaluation_id)
        if not evaluation:
            return None
        
        # 生成执行摘要
        summary = self._generate_executive_summary(evaluation)
        
        # 提取关键指标
        key_metrics = {
            "综合竞争力得分": evaluation.overall_score,
            "7S模型得分": evaluation.seven_s_overall_score,
            "现金流评分": evaluation.cash_flow_score,
            "杜邦评分": evaluation.dupont_score,
            "波特五力评分": evaluation.porter_score
        }
        
        # 生成风险提示
        risk_alerts = self._generate_risk_alerts(evaluation)
        
        # 生成改进建议
        priorities = self._generate_improvement_priorities(evaluation)
        
        return EvaluationReport(
            enterprise_evaluation=evaluation,
            executive_summary=summary,
            key_metrics=key_metrics,
            risk_alerts=risk_alerts,
            improvement_priorities=priorities
        )
    
    def _generate_executive_summary(self, evaluation: EnterpriseEvaluation) -> str:
        """生成执行摘要"""
        level = evaluation.competitiveness_level
        score = evaluation.overall_score
        
        if level == "优秀":
            return f"该企业在本次评估中表现{level}，综合得分{score:.1f}分，处于行业领先水平。"
        elif level == "良好":
            return f"该企业在本次评估中表现{level}，综合得分{score:.1f}分，具有较好的竞争力。"
        elif level == "一般":
            return f"该企业在本次评估中表现{level}，综合得分{score:.1f}分，存在一定提升空间。"
        else:
            return f"该企业在本次评估中表现{level}，综合得分{score:.1f}分，需要重点改进。"
    
    def _generate_risk_alerts(self, evaluation: EnterpriseEvaluation) -> List[Dict[str, str]]:
        """生成风险提示"""
        alerts = []
        
        if evaluation.dupont_analysis and evaluation.dupont_analysis.debt_ratio > 70:
            alerts.append({
                "level": "high",
                "type": "财务风险",
                "message": "资产负债率过高，可能存在偿债风险"
            })
        
        if evaluation.cash_flow_analysis:
            if evaluation.cash_flow_analysis.life_cycle_stage.value == "decline":
                alerts.append({
                    "level": "high",
                    "type": "战略风险",
                    "message": "企业处于衰退期，需要转型升级"
                })
            if evaluation.cash_flow_analysis.operating_cash_flow < 0:
                alerts.append({
                    "level": "medium",
                    "type": "经营风险",
                    "message": "经营性现金流为负，需要关注"
                })
        
        return alerts
    
    def _generate_improvement_priorities(self, evaluation: EnterpriseEvaluation) -> List[Dict[str, Any]]:
        """生成改进建议优先级"""
        priorities = []
        
        for score in evaluation.seven_s_scores:
            if score.score < 60:
                priorities.append({
                    "dimension": score.dimension.value,
                    "current_score": score.score,
                    "target_score": 70,
                    "suggestions": score.suggestions,
                    "priority": "high" if score.score < 50 else "medium"
                })
        
        return sorted(priorities, key=lambda x: (0 if x["priority"] == "high" else 1, x["current_score"]))
