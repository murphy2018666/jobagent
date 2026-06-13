"""
企业评价模块测试

测试麦肯锡7S模型、Dickinson现金流模型、杜邦分析和波特五力模型的实现
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from jobagent.domain.enterprise_evaluation import (
    EnterpriseEvaluation,
    SevenSEvaluation,
    CashFlowAnalysis,
    DuPontAnalysis,
    PorterAnalysis,
    CompanyLifeCycle
)
from jobagent.infrastructure.enterprise_evaluator import (
    EnterpriseEvaluationService,
    SevenSAnalyzer,
    DickinsonCashFlowAnalyzer,
    DuPontAnalyzer,
    PorterAnalyzer
)


class TestSevenSAnalyzer:
    """麦肯锡7S模型分析器测试"""

    def test_analyze_all_dimensions(self):
        """测试分析所有7S维度"""
        analyzer = SevenSAnalyzer()
        
        company_data = {
            "strategy_score": 85,
            "structure_score": 78,
            "systems_score": 82,
            "shared_values_score": 88,
            "style_score": 75,
            "staff_score": 80,
            "skills_score": 86
        }
        
        result = analyzer.analyze(company_data)
        
        assert len(result) == 7
        assert sum(eval.score for eval in result) > 0
        overall_score = analyzer.calculate_overall_score(result)
        assert 0 <= overall_score <= 100
        assert overall_score == pytest.approx(82.0, abs=1.0)

    def test_missing_dimensions_returns_default(self):
        """测试缺失维度时返回默认值"""
        analyzer = SevenSAnalyzer()
        
        company_data = {"strategy_score": 80}
        
        result = analyzer.analyze(company_data)
        
        assert len(result) == 7
        # 检查是否有默认值
        assert any(eval.score == 50 for eval in result)


class TestDickinsonCashFlowAnalyzer:
    """Dickinson现金流模型分析器测试"""

    def test_identify_growth_stage(self):
        """测试识别成长期"""
        analyzer = DickinsonCashFlowAnalyzer()
        
        cash_flow_data = {
            "operating_cash_flow": 1000000,
            "investing_cash_flow": -500000,
            "financing_cash_flow": -200000
        }
        
        result = analyzer.analyze(cash_flow_data)
        
        assert result is not None
        assert result.lifecycle_stage in [CompanyLifeCycle.GROWTH, CompanyLifeCycle.MATURE]

    def test_identify_decline_stage(self):
        """测试识别衰退期"""
        analyzer = DickinsonCashFlowAnalyzer()
        
        cash_flow_data = {
            "operating_cash_flow": -100000,
            "investing_cash_flow": 500000,
            "financing_cash_flow": -300000
        }
        
        result = analyzer.analyze(cash_flow_data)
        
        assert result is not None
        assert result.lifecycle_stage == CompanyLifeCycle.DECLINE

    def test_calculate_cash_flow_score(self):
        """测试现金流评分计算"""
        analyzer = DickinsonCashFlowAnalyzer()
        
        result = CashFlowAnalysis(
            lifecycle_stage=CompanyLifeCycle.GROWTH,
            operating_cash_flow=1000000,
            investing_cash_flow=-500000,
            financing_cash_flow=-200000,
            cf_ratio=1.5,
            free_cash_flow=300000
        )
        
        score = analyzer.calculate_score(result)
        
        assert 0 <= score <= 100


class TestDuPontAnalyzer:
    """杜邦分析模型测试"""

    def test_analyze_financial_data(self):
        """测试分析财务数据"""
        analyzer = DuPontAnalyzer()
        
        financial_data = {
            "revenue": 100000000,
            "net_profit": 15000000,
            "total_assets": 200000000,
            "total_liabilities": 80000000
        }
        
        result = analyzer.analyze(financial_data)
        
        assert result is not None
        assert result.net_margin == pytest.approx(0.15, abs=0.01)
        assert result.asset_turnover == pytest.approx(0.5, abs=0.01)
        assert result.equity_multiplier == pytest.approx(1.67, abs=0.01)
        assert result.roe == pytest.approx(0.125, abs=0.01)

    def test_calculate_dupont_score(self):
        """测试杜邦评分计算"""
        analyzer = DuPontAnalyzer()
        
        result = DuPontAnalysis(
            net_margin=0.15,
            gross_margin=0.65,
            operating_margin=0.20,
            asset_turnover=0.5,
            equity_multiplier=1.67,
            roe=0.125,
            roa=0.075,
            current_ratio=2.5,
            debt_ratio=0.4
        )
        
        score = analyzer.calculate_score(result)
        
        assert 0 <= score <= 100


class TestPorterAnalyzer:
    """波特五力模型测试"""

    def test_analyze_industry_data(self):
        """测试分析行业数据"""
        analyzer = PorterAnalyzer()
        
        industry_data = {
            "new_entrant_threat": 30,
            "supplier_power": 40,
            "buyer_power": 35,
            "substitute_threat": 25,
            "rivalry_intensity": 50
        }
        
        result = analyzer.analyze(industry_data)
        
        assert result is not None
        assert result.new_entrant_threat == 30
        assert result.supplier_power == 40
        assert result.buyer_power == 35
        assert result.substitute_threat == 25
        assert result.rivalry_intensity == 50

    def test_calculate_porter_score(self):
        """测试波特五力评分计算"""
        analyzer = PorterAnalyzer()
        
        result = PorterAnalysis(
            new_entrant_threat=30,
            supplier_power=40,
            buyer_power=35,
            substitute_threat=25,
            rivalry_intensity=50
        )
        
        score = analyzer.calculate_score(result)
        
        assert 0 <= score <= 100


class TestEnterpriseEvaluationService:
    """企业评价服务测试"""

    @pytest.mark.asyncio
    async def test_evaluate_company(self, mock_company_repo, mock_enterprise_eval_repo):
        """测试执行企业综合评价"""
        service = EnterpriseEvaluationService(mock_company_repo, mock_enterprise_eval_repo)
        
        company_data = {
            "strategy_score": 85,
            "structure_score": 80,
            "systems_score": 75,
            "shared_values_score": 88,
            "style_score": 82,
            "staff_score": 80,
            "skills_score": 85,
            "company_name": "测试公司"
        }
        
        financial_data = {
            "revenue": 100000000,
            "net_profit": 15000000,
            "total_assets": 200000000,
            "total_liabilities": 80000000,
            "operating_cash_flow": 25000000,
            "investing_cash_flow": -10000000,
            "financing_cash_flow": -5000000
        }
        
        industry_data = {
            "new_entrant_threat": 30,
            "supplier_power": 35,
            "buyer_power": 40,
            "substitute_threat": 25,
            "rivalry_intensity": 45
        }
        
        result = await service.evaluate_company(
            company_id="test-company-id",
            company_data=company_data,
            financial_data=financial_data,
            industry_data=industry_data
        )
        
        assert result is not None
        assert result.company_id == "test-company-id"
        assert 0 <= result.overall_score <= 100
        assert result.competitiveness_level in ["优秀", "良好", "一般", "较弱"]
        assert len(result.strengths) > 0

    @pytest.mark.asyncio
    async def test_evaluate_company_without_financial_data(self, mock_company_repo, mock_enterprise_eval_repo):
        """测试无财务数据时的评价"""
        service = EnterpriseEvaluationService(mock_company_repo, mock_enterprise_eval_repo)
        
        company_data = {
            "strategy_score": 80,
            "structure_score": 75,
            "systems_score": 70,
            "shared_values_score": 85,
            "style_score": 78,
            "staff_score": 76,
            "skills_score": 82
        }
        
        result = await service.evaluate_company(
            company_id="test-company-id",
            company_data=company_data,
            financial_data=None,
            industry_data=None
        )
        
        assert result is not None
        assert result.seven_s_overall_score > 0

    @pytest.mark.asyncio
    async def test_generate_report(self, mock_company_repo, mock_enterprise_eval_repo):
        """测试生成评价报告"""
        service = EnterpriseEvaluationService(mock_company_repo, mock_enterprise_eval_repo)
        
        company_data = {
            "strategy_score": 85,
            "structure_score": 80,
            "systems_score": 75,
            "shared_values_score": 88,
            "style_score": 82,
            "staff_score": 80,
            "skills_score": 85
        }
        
        evaluation = await service.evaluate_company(
            company_id="test-company-id",
            company_data=company_data
        )
        
        report = service.generate_report(evaluation)
        
        assert report is not None
        assert evaluation.evaluation_id in report
        assert "综合评价" in report