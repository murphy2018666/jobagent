"""
API集成测试

测试评价模块和匹配模块的API接口
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from jobagent.main import app
from jobagent.domain.entities import Company, Job, Candidate
from jobagent.domain.enterprise_evaluation import EnterpriseEvaluation
from jobagent.domain.candidate_evaluation import CandidateEvaluation


client = TestClient(app)


class TestEnterpriseEvaluationAPI:
    """企业评价API测试"""

    def test_create_enterprise_evaluation(self, monkeypatch):
        """测试创建企业评价"""
        async def mock_evaluate_company(*args, **kwargs):
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
        
        monkeypatch.setattr(
            "jobagent.interfaces.evaluation_api.EnterpriseEvaluationApplicationService.evaluate_company",
            mock_evaluate_company
        )
        
        response = client.post(
            "/api/v1/evaluations/enterprise",
            json={
                "company_id": "test-company-id",
                "company_data": {
                    "strategy_score": 85,
                    "structure_score": 80,
                    "systems_score": 75,
                    "shared_values_score": 88,
                    "style_score": 82,
                    "staff_score": 80,
                    "skills_score": 85
                },
                "include_financial": True,
                "include_industry": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["company_id"] == "test-company-id"
        assert data["overall_score"] == 81.25
        assert data["competitiveness_level"] == "优秀"

    def test_get_enterprise_evaluation_history(self, monkeypatch):
        """测试获取企业评价历史"""
        async def mock_get_by_company_id(*args, **kwargs):
            return [
                EnterpriseEvaluation(
                    company_id="test-company-id",
                    evaluation_id="eval-1",
                    overall_score=85.0,
                    competitiveness_level="优秀"
                ),
                EnterpriseEvaluation(
                    company_id="test-company-id",
                    evaluation_id="eval-2",
                    overall_score=80.0,
                    competitiveness_level="良好"
                )
            ]
        
        monkeypatch.setattr(
            "jobagent.interfaces.evaluation_api.EnterpriseEvaluationApplicationService.get_evaluations_by_company",
            mock_get_by_company_id
        )
        
        response = client.get("/api/v1/evaluations/enterprise/test-company-id")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_latest_enterprise_evaluation(self, monkeypatch):
        """测试获取企业最新评价"""
        async def mock_get_latest(*args, **kwargs):
            return EnterpriseEvaluation(
                company_id="test-company-id",
                evaluation_id="latest-eval",
                overall_score=88.0,
                competitiveness_level="优秀"
            )
        
        monkeypatch.setattr(
            "jobagent.interfaces.evaluation_api.EnterpriseEvaluationApplicationService.get_latest_evaluation",
            mock_get_latest
        )
        
        response = client.get("/api/v1/evaluations/enterprise/latest/test-company-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["overall_score"] == 88.0


class TestCandidateEvaluationAPI:
    """候选人评价API测试"""

    def test_create_candidate_evaluation(self, monkeypatch):
        """测试创建候选人评价"""
        async def mock_evaluate_candidate(*args, **kwargs):
            return CandidateEvaluation(
                candidate_id="test-candidate-id",
                job_id="test-job-id",
                evaluation_id="test-cand-eval-id",
                final_score=85.0,
                percentile=90.0,
                evaluation_level="A",
                recommendation="strong_buy"
            )
        
        monkeypatch.setattr(
            "jobagent.interfaces.evaluation_api.CandidateEvaluationApplicationService.evaluate_candidate",
            mock_evaluate_candidate
        )
        
        response = client.post(
            "/api/v1/evaluations/candidate",
            json={
                "candidate_id": "test-candidate-id",
                "job_id": "test-job-id",
                "perform_deep_assessment": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["candidate_id"] == "test-candidate-id"
        assert data["job_id"] == "test-job-id"
        assert data["final_score"] == 85.0
        assert data["evaluation_level"] == "A"

    def test_get_candidate_evaluation(self, monkeypatch):
        """测试获取候选人评价详情"""
        async def mock_get_by_id(*args, **kwargs):
            return CandidateEvaluation(
                candidate_id="test-candidate-id",
                job_id="test-job-id",
                evaluation_id="test-eval-id",
                final_score=80.0,
                percentile=85.0,
                evaluation_level="B",
                recommendation="buy"
            )
        
        monkeypatch.setattr(
            "jobagent.interfaces.evaluation_api.CandidateEvaluationApplicationService.get_evaluation",
            mock_get_by_id
        )
        
        response = client.get("/api/v1/evaluations/candidate/test-eval-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["evaluation_level"] == "B"

    def test_get_initial_screening_result(self, monkeypatch):
        """测试获取初筛结果"""
        from jobagent.domain.candidate_evaluation import InitialScreeningResult
        
        async def mock_get_by_id(*args, **kwargs):
            return CandidateEvaluation(
                candidate_id="test-id",
                job_id="test-job",
                evaluation_id="test-eval",
                initial_screening=InitialScreeningResult(
                    screening_id="screen-1",
                    hard_filter_passed=True,
                    hard_filter_score=90,
                    semantic_match_score=85,
                    overall_score=87
                )
            )
        
        monkeypatch.setattr(
            "jobagent.interfaces.evaluation_api.CandidateEvaluationApplicationService.get_evaluation",
            mock_get_by_id
        )
        
        response = client.get("/api/v1/evaluations/candidate/initial/test-eval")
        
        assert response.status_code == 200
        data = response.json()
        assert data["hard_filter_passed"] is True
        assert data["overall_score"] == 87


class TestMatchingAPI:
    """匹配API测试"""

    def test_match_candidates(self, monkeypatch):
        """测试匹配候选人"""
        from jobagent.domain.entities import MatchingResult
        
        async def mock_match(*args, **kwargs):
            return [
                MatchingResult(
                    id="match-1",
                    job_id="test-job-id",
                    candidate_id="c1",
                    score=90.5,
                    rank=1,
                    match_reasons=["技能匹配度高", "经验匹配"]
                ),
                MatchingResult(
                    id="match-2",
                    job_id="test-job-id",
                    candidate_id="c2",
                    score=85.0,
                    rank=2,
                    match_reasons=["技能匹配"]
                )
            ]
        
        monkeypatch.setattr(
            "jobagent.interfaces.api.MatchingService.match_candidates",
            mock_match
        )
        
        response = client.post(
            "/api/v1/match",
            json={"job_id": "test-job-id", "top_n": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["score"] == 90.5

    def test_get_match_result(self, monkeypatch):
        """测试获取匹配结果"""
        from jobagent.domain.entities import MatchingResult
        
        async def mock_get(*args, **kwargs):
            return MatchingResult(
                id="test-match-id",
                job_id="test-job-id",
                candidate_id="test-candidate-id",
                score=88.0,
                rank=1
            )
        
        monkeypatch.setattr(
            "jobagent.interfaces.api.MatchingService.get_match_result",
            mock_get
        )
        
        response = client.get("/api/v1/match/test-match-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 88.0


class TestHealthAPI:
    """健康检查API测试"""

    def test_health_check(self):
        """测试健康检查接口"""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"