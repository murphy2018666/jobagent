"""
候选人评价模块测试

测试初筛Agent、深度评估Agent和综合评价的实现
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from jobagent.domain.candidate_evaluation import (
    CandidateEvaluation,
    InitialScreeningResult,
    DeepAssessmentResult,
    IcebergDimensionScore,
    EvaluationStage,
    EvaluationLevel
)
from jobagent.domain.entities import Candidate, Job
from jobagent.infrastructure.candidate_evaluator import (
    CandidateEvaluationService,
    InitialScreeningAgent,
    DeepAssessmentAgent
)


class TestInitialScreeningAgent:
    """初筛Agent测试"""

    def test_resume_parsing(self):
        """测试简历解析"""
        agent = InitialScreeningAgent()
        
        resume_text = """
        姓名：张三
        电话：13800138000
        邮箱：zhangsan@example.com
        学历：本科
        工作经验：5年
        技能：Python, Java, SQL
        """
        
        result = agent.parse_resume(resume_text)
        
        assert result is not None
        assert result["name"] == "张三"
        assert "skills" in result
        assert len(result["skills"]) >= 1

    def test_hard_filter_pass(self):
        """测试硬性条件过滤通过"""
        agent = InitialScreeningAgent()
        
        candidate_data = {
            "education": "本科",
            "experience": 5,
            "skills": ["Python", "FastAPI", "SQL"],
            "location": "北京",
            "salary_expectation": 20000
        }
        
        job_requirements = {
            "education": "本科",
            "experience": 3,
            "skills": ["Python", "FastAPI"],
            "location": "北京",
            "salary_min": 15000,
            "salary_max": 25000
        }
        
        result = agent.hard_filter(candidate_data, job_requirements)
        
        assert result is not None
        assert result["passed"] is True
        assert len(result["matched_conditions"]) >= 4

    def test_hard_filter_fail(self):
        """测试硬性条件过滤失败"""
        agent = InitialScreeningAgent()
        
        candidate_data = {
            "education": "专科",
            "experience": 2,
            "skills": ["Java"],
            "location": "上海",
            "salary_expectation": 30000
        }
        
        job_requirements = {
            "education": "本科",
            "experience": 3,
            "skills": ["Python", "FastAPI"],
            "location": "北京",
            "salary_min": 15000,
            "salary_max": 25000
        }
        
        result = agent.hard_filter(candidate_data, job_requirements)
        
        assert result is not None
        assert result["passed"] is False
        assert len(result["failed_conditions"]) > 0

    def test_semantic_matching(self):
        """测试语义匹配"""
        agent = InitialScreeningAgent()
        
        job_description = "负责后端开发，使用Python和FastAPI构建RESTful API"
        candidate_profile = "5年Python开发经验，精通FastAPI框架，熟悉RESTful API设计"
        
        score = agent.semantic_match(job_description, candidate_profile)
        
        assert 0 <= score <= 100
        assert score > 50  # 应该有较高匹配度

    def test_calculate_initial_score(self):
        """测试初筛得分计算"""
        agent = InitialScreeningAgent()
        
        screening_data = {
            "hard_filter_passed": True,
            "hard_filter_score": 90,
            "semantic_match_score": 85,
            "skill_match_score": 88,
            "experience_match_score": 92
        }
        
        score = agent.calculate_score(screening_data)
        
        assert 0 <= score <= 100
        assert score == pytest.approx(87.2, abs=1.0)


class TestDeepAssessmentAgent:
    """深度评估Agent测试"""

    def test_generate_interview_questions(self):
        """测试生成面试问题"""
        agent = DeepAssessmentAgent()
        
        job_requirements = {
            "title": "高级软件工程师",
            "skills": ["Python", "FastAPI", "系统设计"],
            "experience": 5
        }
        
        questions = agent.generate_questions(job_requirements, count=5)
        
        assert len(questions) == 5
        for q in questions:
            assert "question" in q
            assert "dimension" in q
            assert "expected_behavior" in q

    def test_analyze_soft_skills(self):
        """测试软素质分析"""
        agent = DeepAssessmentAgent()
        
        interview_responses = {
            "leadership": "我曾经带领5人团队完成了一个重要项目...",
            "teamwork": "在项目中我积极与其他部门协作...",
            "problem_solving": "遇到技术难题时，我会先分析问题根源...",
            "communication": "我善于与非技术人员沟通..."
        }
        
        result = agent.analyze_soft_skills(interview_responses)
        
        assert result is not None
        assert "leadership" in result
        assert "teamwork" in result
        assert "problem_solving" in result
        assert 0 <= result["leadership"] <= 100

    def test_calculate_cultural_fit(self):
        """测试文化匹配度计算"""
        agent = DeepAssessmentAgent()
        
        candidate_values = ["创新", "团队合作", "客户至上"]
        company_values = ["创新", "卓越", "团队合作", "诚信"]
        
        score = agent.calculate_cultural_fit(candidate_values, company_values)
        
        assert 0 <= score <= 100
        assert score == pytest.approx(66.7, abs=1.0)

    def test_assess_growth_potential(self):
        """测试成长潜力评估"""
        agent = DeepAssessmentAgent()
        
        candidate_data = {
            "learning_history": ["自学Python", "获得认证", "参与开源项目"],
            "career_progress": "从初级工程师晋升到高级工程师",
            "self_development": "每周学习新技术",
            "ambition_level": "高"
        }
        
        score = agent.assess_growth_potential(candidate_data)
        
        assert 0 <= score <= 100

    def test_calculate_deep_score(self):
        """测试深度评估得分计算"""
        agent = DeepAssessmentAgent()
        
        assessment_data = {
            "knowledge_score": 85,
            "skills_score": 88,
            "self_knowledge_score": 78,
            "traits_score": 82,
            "motives_score": 80,
            "values_score": 85,
            "cultural_fit_score": 82,
            "growth_potential_score": 85
        }
        
        score = agent.calculate_score(assessment_data)
        
        assert 0 <= score <= 100


class TestCandidateEvaluationService:
    """候选人评价服务测试"""

    @pytest.mark.asyncio
    async def test_evaluate_candidate_full(self, mock_candidate_repo, mock_job_repo, mock_candidate_eval_repo):
        """测试完整的候选人评价流程"""
        service = CandidateEvaluationService(mock_candidate_repo, mock_job_repo, mock_candidate_eval_repo)
        
        # 设置mock返回值
        mock_candidate_repo.get_by_id.return_value = Candidate(
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
        
        mock_job_repo.get_by_id.return_value = Job(
            id="test-job-id",
            company_id="test-company-id",
            title="高级软件工程师",
            description="负责后端开发",
            requirements={"skills": ["Python", "FastAPI"], "experience": 3, "education": "本科"},
            status="open"
        )
        
        result = await service.evaluate_candidate(
            candidate_id="test-candidate-id",
            job_id="test-job-id",
            perform_deep_assessment=True
        )
        
        assert result is not None
        assert result.candidate_id == "test-candidate-id"
        assert result.job_id == "test-job-id"
        assert result.current_stage == EvaluationStage.COMPLETED
        assert 0 <= result.final_score <= 100
        assert result.evaluation_level in ["A", "B", "C", "D"]

    @pytest.mark.asyncio
    async def test_evaluate_candidate_only_initial(self, mock_candidate_repo, mock_job_repo, mock_candidate_eval_repo):
        """测试仅执行初筛"""
        service = CandidateEvaluationService(mock_candidate_repo, mock_job_repo, mock_candidate_eval_repo)
        
        mock_candidate_repo.get_by_id.return_value = Candidate(
            id="test-candidate-id",
            name="李四",
            email="lisi@example.com",
            phone="13900139000",
            resume="简历内容...",
            skills=["Java"],
            experience=2,
            education="专科",
            salary_expectation=15000
        )
        
        mock_job_repo.get_by_id.return_value = Job(
            id="test-job-id",
            company_id="test-company-id",
            title="高级软件工程师",
            description="负责后端开发",
            requirements={"skills": ["Python", "FastAPI"], "experience": 3},
            status="open"
        )
        
        result = await service.evaluate_candidate(
            candidate_id="test-candidate-id",
            job_id="test-job-id",
            perform_deep_assessment=False
        )
        
        assert result is not None
        assert result.current_stage == EvaluationStage.INITIAL_SCREENING
        assert result.initial_screening is not None

    @pytest.mark.asyncio
    async def test_calculate_final_score(self, mock_candidate_repo, mock_job_repo, mock_candidate_eval_repo):
        """测试综合得分计算"""
        service = CandidateEvaluationService(mock_candidate_repo, mock_job_repo, mock_candidate_eval_repo)
        
        screening = InitialScreeningResult(
            screening_id="test-screening-id",
            hard_filter_passed=True,
            hard_filter_score=85,
            semantic_match_score=80,
            skill_match_score=88,
            experience_match_score=82,
            overall_score=83.2
        )
        
        assessment = DeepAssessmentResult(
            assessment_id="test-assessment-id",
            iceberg_scores={
                "knowledge": IcebergDimensionScore(dimension="knowledge", score=85, description="专业知识扎实"),
                "skills": IcebergDimensionScore(dimension="skills", score=88, description="技术能力强"),
                "self_knowledge": IcebergDimensionScore(dimension="self_knowledge", score=78, description="自我认知清晰"),
                "traits": IcebergDimensionScore(dimension="traits", score=82, description="性格良好"),
                "motives": IcebergDimensionScore(dimension="motives", score=80, description="动机明确"),
                "values": IcebergDimensionScore(dimension="values", score=85, description="价值观匹配")
            },
            cultural_fit_score=82,
            growth_potential_score=85,
            overall_score=84.0
        )
        
        evaluation = CandidateEvaluation(
            candidate_id="test-candidate-id",
            job_id="test-job-id",
            evaluation_id="test-eval-id",
            initial_screening=screening,
            deep_assessment=assessment,
            initial_screening_weight=0.4,
            deep_assessment_weight=0.6
        )
        
        final_score = service._calculate_final_score(evaluation)
        
        expected_score = 83.2 * 0.4 + 84.0 * 0.6
        assert final_score == pytest.approx(expected_score, abs=0.1)

    @pytest.mark.asyncio
    async def test_determine_evaluation_level(self, mock_candidate_repo, mock_job_repo, mock_candidate_eval_repo):
        """测试评价等级确定"""
        service = CandidateEvaluationService(mock_candidate_repo, mock_job_repo, mock_candidate_eval_repo)
        
        # 测试A等级
        eval_a = CandidateEvaluation(
            candidate_id="test-id",
            job_id="test-job",
            evaluation_id="test-eval",
            final_score=90
        )
        level_a = service._determine_evaluation_level(eval_a)
        assert level_a == EvaluationLevel.A
        
        # 测试B等级
        eval_b = CandidateEvaluation(
            candidate_id="test-id",
            job_id="test-job",
            evaluation_id="test-eval",
            final_score=75
        )
        level_b = service._determine_evaluation_level(eval_b)
        assert level_b == EvaluationLevel.B
        
        # 测试C等级
        eval_c = CandidateEvaluation(
            candidate_id="test-id",
            job_id="test-job",
            evaluation_id="test-eval",
            final_score=60
        )
        level_c = service._determine_evaluation_level(eval_c)
        assert level_c == EvaluationLevel.C
        
        # 测试D等级
        eval_d = CandidateEvaluation(
            candidate_id="test-id",
            job_id="test-job",
            evaluation_id="test-eval",
            final_score=50
        )
        level_d = service._determine_evaluation_level(eval_d)
        assert level_d == EvaluationLevel.D

    @pytest.mark.asyncio
    async def test_generate_evaluation_report(self, mock_candidate_repo, mock_job_repo, mock_candidate_eval_repo):
        """测试生成评价报告"""
        service = CandidateEvaluationService(mock_candidate_repo, mock_job_repo, mock_candidate_eval_repo)
        
        evaluation = CandidateEvaluation(
            candidate_id="test-candidate-id",
            job_id="test-job-id",
            evaluation_id="test-eval-id",
            final_score=85,
            percentile=90,
            evaluation_level="A",
            recommendation="strong_buy",
            evaluation_summary="综合评价优秀，强烈推荐"
        )
        
        report = service.generate_report(evaluation)
        
        assert report is not None
        assert evaluation.evaluation_id in report
        assert "综合评价" in report
        assert "最终得分" in report