"""
匹配引擎模块测试

测试匹配算法、相似度计算和结果排序的实现
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from jobagent.domain.entities import Candidate, Job
from jobagent.domain.services import MatchingService
from jobagent.infrastructure.matching_engine import (
    MatchingEngine,
    SemanticMatcher,
    SkillMatcher,
    ExperienceMatcher,
    EducationMatcher
)


class TestSkillMatcher:
    """技能匹配器测试"""

    def test_exact_match(self):
        """测试精确匹配"""
        matcher = SkillMatcher()
        
        job_skills = ["Python", "FastAPI", "SQL"]
        candidate_skills = ["Python", "FastAPI", "SQL", "Redis"]
        
        score = matcher.match(job_skills, candidate_skills)
        
        assert 0 <= score <= 100
        assert score >= 80  # 所有必需技能都匹配

    def test_partial_match(self):
        """测试部分匹配"""
        matcher = SkillMatcher()
        
        job_skills = ["Python", "FastAPI", "SQL", "Docker"]
        candidate_skills = ["Python", "Flask", "SQL"]
        
        score = matcher.match(job_skills, candidate_skills)
        
        assert 0 <= score <= 100
        assert 50 <= score < 80  # 部分匹配

    def test_no_match(self):
        """测试无匹配"""
        matcher = SkillMatcher()
        
        job_skills = ["Java", "Spring", "Oracle"]
        candidate_skills = ["Python", "FastAPI", "PostgreSQL"]
        
        score = matcher.match(job_skills, candidate_skills)
        
        assert 0 <= score < 50  # 无匹配


class TestExperienceMatcher:
    """经验匹配器测试"""

    def test_exact_experience_match(self):
        """测试经验完全匹配"""
        matcher = ExperienceMatcher()
        
        job_requirement = {"min_experience": 3, "max_experience": 5}
        candidate_experience = 4
        
        score = matcher.match(job_requirement, candidate_experience)
        
        assert score >= 90

    def test_experience_above_max(self):
        """测试经验超过上限"""
        matcher = ExperienceMatcher()
        
        job_requirement = {"min_experience": 2, "max_experience": 4}
        candidate_experience = 6
        
        score = matcher.match(job_requirement, candidate_experience)
        
        assert 70 <= score < 90

    def test_experience_below_min(self):
        """测试经验低于下限"""
        matcher = ExperienceMatcher()
        
        job_requirement = {"min_experience": 3, "max_experience": 5}
        candidate_experience = 2
        
        score = matcher.match(job_requirement, candidate_experience)
        
        assert 40 <= score < 70


class TestEducationMatcher:
    """学历匹配器测试"""

    def test_education_exact_match(self):
        """测试学历完全匹配"""
        matcher = EducationMatcher()
        
        job_requirement = "本科"
        candidate_education = "本科"
        
        score = matcher.match(job_requirement, candidate_education)
        
        assert score >= 90

    def test_education_above_requirement(self):
        """测试学历高于要求"""
        matcher = EducationMatcher()
        
        job_requirement = "本科"
        candidate_education = "硕士"
        
        score = matcher.match(job_requirement, candidate_education)
        
        assert score >= 90

    def test_education_below_requirement(self):
        """测试学历低于要求"""
        matcher = EducationMatcher()
        
        job_requirement = "本科"
        candidate_education = "专科"
        
        score = matcher.match(job_requirement, candidate_education)
        
        assert 40 <= score < 70


class TestSemanticMatcher:
    """语义匹配器测试"""

    def test_high_similarity(self):
        """测试高相似度"""
        matcher = SemanticMatcher()
        
        job_desc = "负责使用Python和FastAPI开发后端API服务"
        candidate_desc = "5年Python开发经验，精通FastAPI框架，擅长构建RESTful API"
        
        score = matcher.match(job_desc, candidate_desc)
        
        assert score >= 70

    def test_low_similarity(self):
        """测试低相似度"""
        matcher = SemanticMatcher()
        
        job_desc = "负责前端页面开发，使用React和TypeScript"
        candidate_desc = "3年Java后端开发经验，熟悉Spring Boot框架"
        
        score = matcher.match(job_desc, candidate_desc)
        
        assert score < 50


class TestMatchingEngine:
    """匹配引擎测试"""

    def test_single_candidate_match(self):
        """测试单个候选人匹配"""
        engine = MatchingEngine()
        
        job = Job(
            id="test-job-id",
            company_id="test-company-id",
            title="高级Python工程师",
            description="负责后端API开发，使用Python和FastAPI",
            requirements={
                "skills": ["Python", "FastAPI", "SQL"],
                "experience": 3,
                "education": "本科"
            },
            status="open"
        )
        
        candidate = Candidate(
            id="test-candidate-id",
            name="张三",
            email="zhangsan@example.com",
            phone="13800138000",
            resume="5年Python开发经验，精通FastAPI...",
            skills=["Python", "FastAPI", "SQL", "Redis"],
            experience=5,
            education="本科",
            salary_expectation=25000
        )
        
        result = engine.match_single(job, candidate)
        
        assert result is not None
        assert result.candidate_id == candidate.id
        assert 0 <= result.score <= 100
        assert result.score >= 80  # 高匹配度

    def test_batch_match(self):
        """测试批量匹配"""
        engine = MatchingEngine()
        
        job = Job(
            id="test-job-id",
            company_id="test-company-id",
            title="Python工程师",
            description="使用Python开发后端服务",
            requirements={
                "skills": ["Python"],
                "experience": 2,
                "education": "本科"
            },
            status="open"
        )
        
        candidates = [
            Candidate(
                id="c1",
                name="张三",
                email="zhangsan@example.com",
                phone="13800138000",
                resume="简历1",
                skills=["Python", "FastAPI"],
                experience=3,
                education="本科",
                salary_expectation=20000
            ),
            Candidate(
                id="c2",
                name="李四",
                email="lisi@example.com",
                phone="13900139000",
                resume="简历2",
                skills=["Java"],
                experience=2,
                education="专科",
                salary_expectation=15000
            ),
            Candidate(
                id="c3",
                name="王五",
                email="wangwu@example.com",
                phone="13700137000",
                resume="简历3",
                skills=["Python", "Django", "SQL"],
                experience=5,
                education="硕士",
                salary_expectation=30000
            )
        ]
        
        results = engine.batch_match(job, candidates, top_n=2)
        
        assert len(results) == 2
        assert results[0].score >= results[1].score  # 按得分排序
        assert results[0].candidate_id == "c3"  # 王五应该得分最高

    def test_calculate_weighted_score(self):
        """测试加权得分计算"""
        engine = MatchingEngine()
        
        dimension_scores = {
            "skill_match": 85,
            "experience_match": 90,
            "education_match": 100,
            "location_match": 80,
            "salary_match": 75
        }
        
        weights = {
            "skill_match": 0.35,
            "experience_match": 0.25,
            "education_match": 0.15,
            "location_match": 0.10,
            "salary_match": 0.10
        }
        
        score = engine._calculate_weighted_score(dimension_scores, weights)
        
        expected = 85 * 0.35 + 90 * 0.25 + 100 * 0.15 + 80 * 0.10 + 75 * 0.10
        assert score == pytest.approx(expected, abs=0.1)


class TestMatchingService:
    """匹配服务测试"""

    @pytest.mark.asyncio
    async def test_match_candidates(self):
        """测试候选人和岗位匹配"""
        mock_candidate_repo = AsyncMock()
        mock_job_repo = AsyncMock()
        mock_result_repo = AsyncMock()
        
        service = MatchingService(mock_candidate_repo, mock_job_repo, mock_result_repo)
        
        job = Job(
            id="test-job-id",
            company_id="test-company-id",
            title="测试岗位",
            description="测试描述",
            requirements={"skills": ["Python"]},
            status="open"
        )
        
        candidates = [
            Candidate(
                id="c1",
                name="张三",
                email="zhangsan@example.com",
                phone="13800138000",
                resume="简历",
                skills=["Python"],
                experience=3,
                education="本科",
                salary_expectation=20000
            )
        ]
        
        mock_job_repo.get_by_id.return_value = job
        mock_candidate_repo.search_by_job_requirements.return_value = candidates
        
        result = await service.match_candidates("test-job-id", top_n=10)
        
        assert result is not None
        assert len(result) == 1
        assert result[0].candidate_id == "c1"

    @pytest.mark.asyncio
    async def test_update_match_result(self):
        """测试更新匹配结果"""
        mock_candidate_repo = AsyncMock()
        mock_job_repo = AsyncMock()
        mock_result_repo = AsyncMock()
        
        service = MatchingService(mock_candidate_repo, mock_job_repo, mock_result_repo)
        
        result_id = "test-result-id"
        status = "matched"
        
        await service.update_match_result(result_id, status)
        
        mock_result_repo.update_status.assert_called_once_with(result_id, status)