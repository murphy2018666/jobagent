"""
测试配置文件

包含pytest fixture定义和测试工具函数
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from jobagent.domain.entities import Company, Candidate, Job
from jobagent.domain.enterprise_evaluation import EnterpriseEvaluation
from jobagent.domain.candidate_evaluation import CandidateEvaluation
from jobagent.domain.repositories import (
    CompanyRepository,
    CandidateRepository,
    JobRepository,
    MatchingResultRepository,
    TaskRepository
)
from jobagent.domain.evaluation_repositories import (
    EnterpriseEvaluationRepository,
    CandidateEvaluationRepository
)


@pytest.fixture
def mock_company_repo():
    """模拟企业仓储"""
    repo = AsyncMock(spec=CompanyRepository)
    return repo


@pytest.fixture
def mock_candidate_repo():
    """模拟候选人仓储"""
    repo = AsyncMock(spec=CandidateRepository)
    return repo


@pytest.fixture
def mock_job_repo():
    """模拟岗位仓储"""
    repo = AsyncMock(spec=JobRepository)
    return repo


@pytest.fixture
def mock_enterprise_eval_repo():
    """模拟企业评价仓储"""
    repo = AsyncMock(spec=EnterpriseEvaluationRepository)
    return repo


@pytest.fixture
def mock_candidate_eval_repo():
    """模拟候选人评价仓储"""
    repo = AsyncMock(spec=CandidateEvaluationRepository)
    return repo


@pytest.fixture
def sample_company():
    """示例企业数据"""
    return Company(
        id="test-company-id",
        name="测试企业",
        mcp_server_url="http://localhost:8080",
        api_key="test-api-key",
        status="active"
    )


@pytest.fixture
def sample_job():
    """示例岗位数据"""
    return Job(
        id="test-job-id",
        company_id="test-company-id",
        title="高级软件工程师",
        description="负责后端开发",
        requirements={"skills": ["Python", "FastAPI"], "experience": 3},
        status="open"
    )


@pytest.fixture
def sample_candidate():
    """示例候选人数据"""
    return Candidate(
        id="test-candidate-id",
        name="张三",
        email="zhangsan@example.com",
        phone="13800138000",
        resume="简历内容...",
        skills=["Python", "FastAPI", "SQL"],
        experience=5,
        education="本科",
        salary_expectation=20000
    )


@pytest.fixture
def sample_enterprise_evaluation():
    """示例企业评价数据"""
    return EnterpriseEvaluation(
        company_id="test-company-id",
        evaluation_id="test-eval-id",
        seven_s_overall_score=85.0,
        cash_flow_score=78.0,
        dupont_score=82.0,
        porter_score=80.0,
        overall_score=81.25,
        competitiveness_level="优秀"
    )


@pytest.fixture
def sample_candidate_evaluation():
    """示例候选人评价数据"""
    return CandidateEvaluation(
        candidate_id="test-candidate-id",
        job_id="test-job-id",
        evaluation_id="test-cand-eval-id",
        final_score=85.0,
        percentile=90.0,
        evaluation_level="A",
        recommendation="strong_buy"
    )


@pytest.fixture
def sample_company_data():
    """示例企业数据字典"""
    return {
        "company_name": "测试科技有限公司",
        "industry": "互联网",
        "scale": "500-1000人",
        "founded_year": 2015,
        "business_description": "专注于AI技术研发",
        "market_position": "行业领先",
        "branding_score": 85,
        "innovation_capability": 90,
        "management_maturity": 80,
        "employee_satisfaction": 75
    }


@pytest.fixture
def sample_financial_data():
    """示例财务数据"""
    return {
        "revenue": 100000000,
        "net_profit": 15000000,
        "total_assets": 200000000,
        "total_liabilities": 80000000,
        "operating_cash_flow": 25000000,
        "investing_cash_flow": -10000000,
        "financing_cash_flow": 5000000,
        "gross_margin": 65.0,
        "net_margin": 15.0,
        "asset_turnover": 0.5,
        "roe": 12.5,
        "current_ratio": 2.5,
        "debt_ratio": 0.4
    }


@pytest.fixture
def sample_industry_data():
    """示例行业数据"""
    return {
        "industry_name": "人工智能",
        "market_size": 50000000000,
        "growth_rate": 25.0,
        "competitor_count": 500,
        "entry_barrier": "高",
        "tech_change_speed": "快",
        "regulatory_env": "中等",
        "average_profit_margin": 20.0
    }


@pytest.fixture
def sample_resume_text():
    """示例简历文本"""
    return """
    个人信息
    姓名：李四
    电话：13900139000
    邮箱：lisi@example.com
    
    教育背景
    2015-2019 清华大学 计算机科学与技术 本科
    
    工作经历
    2019-至今 字节跳动 高级工程师
    - 负责推荐系统架构设计
    - 优化算法性能，提升推荐准确率30%
    - 带领5人团队完成多个核心项目
    
    技能
    - 编程语言：Python, Java, Go
    - 技术栈：Redis, Kafka, Spark, TensorFlow
    - 框架：Spring Boot, FastAPI
    """


@pytest.fixture
def event_loop():
    """创建事件循环"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()