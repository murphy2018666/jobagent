"""
候选人评价服务实现

实现基于"双Agent协同评价模型"的候选人综合评价：
1. 初筛Agent：基于量化人岗匹配模型，完成简历结构化提取、硬性条件过滤、语义匹配打分
2. 深度评估Agent：基于冰山模型+STAR框架，生成面试题并做软素质量化评分
3. 最终汇总：整合初筛得分+深度评估得分，输出完整评价报告
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import re
from loguru import logger

from ..domain.candidate_evaluation import (
    CandidateEvaluation, CandidateEvaluationReport,
    InitialScreeningResult, DeepAssessmentResult,
    StructuredResume, HardConditionFilter, SemanticMatchResult,
    SoftQualityDimension, StarResponse, InterviewQuestion,
    IcebergDimension, EvaluationStage
)
from ..domain.entities import Candidate, Job
from ..domain.repositories import CandidateRepository, JobRepository
from ..domain.evaluation_repositories import CandidateEvaluationRepository


class ResumeParser:
    """
    简历解析器
    
    从原始简历文本中提取结构化信息。
    """
    
    def parse(self, resume_text: str, candidate_id: str) -> StructuredResume:
        """
        解析简历
        
        Args:
            resume_text: 原始简历文本
            candidate_id: 候选人ID
            
        Returns:
            StructuredResume: 结构化简历数据
        """
        resume = StructuredResume(candidate_id=candidate_id)
        
        # 提取基本信息
        resume.raw_resume_text = resume_text
        resume.name = self._extract_name(resume_text)
        resume.age = self._extract_age(resume_text)
        resume.location = self._extract_location(resume_text)
        
        # 提取教育背景
        education = self._extract_education(resume_text)
        resume.education = education
        if education:
            resume.highest_degree = education[0].get("degree", "")
            resume.graduate_school = education[0].get("school", "")
            resume.major = education[0].get("major", "")
        
        # 提取工作经历
        work_experience = self._extract_work_experience(resume_text)
        resume.work_experience = work_experience
        resume.total_years = self._calculate_total_years(work_experience)
        if work_experience:
            resume.current_company = work_experience[0].get("company", "")
            resume.current_position = work_experience[0].get("position", "")
        
        # 提取技能
        resume.hard_skills = self._extract_hard_skills(resume_text)
        resume.soft_skills = self._extract_soft_skills(resume_text)
        resume.certifications = self._extract_certifications(resume_text)
        
        # 提取项目经历
        resume.projects = self._extract_projects(resume_text)
        
        # 计算提取置信度
        resume.extraction_confidence = self._calculate_confidence(resume)
        
        return resume
    
    def _extract_name(self, text: str) -> str:
        """提取姓名"""
        patterns = [
            r"姓名[：:]\s*([^\n]+)",
            r"^([\u4e00-\u9fa5]{2,4})$",  # 行首的中文名
        ]
        for pattern in patterns:
            match = re.search(pattern, text[:200])
            if match:
                return match.group(1).strip()
        return ""
    
    def _extract_age(self, text: str) -> Optional[int]:
        """提取年龄"""
        patterns = [
            r"年龄[：:]\s*(\d+)",
            r"(\d{2})岁",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        return None
    
    def _extract_location(self, text: str) -> str:
        """提取地点"""
        patterns = [
            r"地址[：:]\s*([^\n]+)",
            r"所在地[：:]\s*([^\n]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        return ""
    
    def _extract_education(self, text: str) -> List[Dict[str, Any]]:
        """提取教育背景"""
        education = []
        patterns = [
            r"(\d{4}).*?(\d{4})[^学]*?学[^\n]*?(本科|硕士|博士|大专|高中|中专|初中)",
            r"(本科|硕士|博士|大专)[^\n]*?([^\n]+?大学)",
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) >= 3:
                    education.append({
                        "period": f"{match[0]}-{match[1]}",
                        "degree": match[2],
                        "school": match[1] if len(match) > 1 else ""
                    })
        return education[:3]  # 最多3段教育经历
    
    def _extract_work_experience(self, text: str) -> List[Dict[str, Any]]:
        """提取工作经历"""
        experience = []
        # 简单的时间线提取
        time_pattern = r"(\d{4}[年-]\d{1,2}月?)"
        company_pattern = r"([A-Za-z\u4e00-\u9fa5]+(?:公司|企业|集团|有限|股份))"
        position_pattern = r"(?:担任|职位|岗位)[：:]\s*([^\n]+)"
        
        return experience[:5]  # 最多5段工作经历
    
    def _calculate_total_years(self, work_experience: List[Dict]) -> float:
        """计算总工作年限"""
        total = 0.0
        for exp in work_experience:
            if "duration" in exp:
                # 解析duration
                duration_str = exp["duration"]
                if "-" in duration_str:
                    years = duration_str.split("-")[-1].strip()
                    if "年" in years:
                        total += float(re.search(r"(\d+\.?\d*)", years).group(1))
        return total
    
    def _extract_hard_skills(self, text: str) -> List[str]:
        """提取硬技能"""
        common_skills = [
            "python", "java", "javascript", "c++", "c#", "go", "rust",
            "sql", "mongodb", "redis", "elasticsearch",
            "react", "vue", "angular", "node.js",
            "docker", "kubernetes", "aws", "azure", "gcp",
            "tensorflow", "pytorch", "scikit-learn",
            "spring", "django", "flask", "fastapi",
            "git", "linux", "nginx", "apache",
            "hadoop", "spark", "kafka", "flink"
        ]
        found_skills = []
        text_lower = text.lower()
        for skill in common_skills:
            if skill in text_lower:
                found_skills.append(skill)
        return found_skills
    
    def _extract_soft_skills(self, text: str) -> List[str]:
        """提取软技能"""
        soft_keywords = [
            "沟通", "协调", "团队合作", "领导力", "Problem Solving",
            "分析", "创新", "适应", "学习能力", "时间管理",
            "责任心", "抗压", "表达", "逻辑思维"
        ]
        found = []
        for keyword in soft_keywords:
            if keyword in text:
                found.append(keyword)
        return found
    
    def _extract_certifications(self, text: str) -> List[str]:
        """提取证书"""
        cert_keywords = [
            "PMP", "CFA", "CPA", "FRM", "ACCA",
            "AWS", "Azure", "GCP",
            "CISP", "CISSP", "CISA",
            "软考", "系统架构设计师", "项目经理"
        ]
        found = []
        for cert in cert_keywords:
            if cert in text:
                found.append(cert)
        return found
    
    def _extract_projects(self, text: str) -> List[Dict[str, Any]]:
        """提取项目经历"""
        projects = []
        project_pattern = r"项目[：:]\s*([^\n]+)"
        matches = re.findall(project_pattern, text)
        for match in matches:
            projects.append({"name": match.strip(), "description": ""})
        return projects
    
    def _calculate_confidence(self, resume: StructuredResume) -> float:
        """计算提取置信度"""
        score = 0.5
        if resume.name: score += 0.1
        if resume.education: score += 0.1
        if resume.work_experience: score += 0.1
        if resume.hard_skills: score += 0.1
        if resume.certifications: score += 0.1
        return min(score, 1.0)


class HardConditionFilterEngine:
    """
    硬性条件过滤器
    
    检查候选人是否满足岗位的基本要求。
    """
    
    def filter(
        self,
        job: Job,
        candidate: Candidate,
        structured_resume: StructuredResume
    ) -> HardConditionFilter:
        """
        执行硬性条件过滤
        
        Args:
            job: 岗位实体
            candidate: 候选人实体
            structured_resume: 结构化简历
            
        Returns:
            HardConditionFilter: 过滤结果
        """
        result = HardConditionFilter(
            job_id=job.id,
            candidate_id=candidate.id
        )
        
        failed_conditions = []
        pass_count = 0
        total_count = 7
        
        # 教育要求
        result.education_met, result.education_detail = self._check_education(
            job, structured_resume
        )
        if not result.education_met:
            failed_conditions.append("学历要求")
        else:
            pass_count += 1
        
        # 经验要求
        result.experience_met, result.experience_detail = self._check_experience(
            job, structured_resume
        )
        if not result.experience_met:
            failed_conditions.append("经验要求")
        else:
            pass_count += 1
        
        # 技能要求
        result.skills_met, result.skills_detail = self._check_skills(
            job, structured_resume
        )
        if not result.skills_met:
            failed_conditions.append("技能要求")
        else:
            pass_count += 1
        
        # 证书要求
        result.certification_met, result.certification_detail = self._check_certification(
            job, structured_resume
        )
        if not result.certification_met:
            failed_conditions.append("证书要求")
        else:
            pass_count += 1
        
        # 地点要求
        result.location_met, result.location_detail = self._check_location(
            job, candidate
        )
        if not result.location_met:
            failed_conditions.append("地点要求")
        else:
            pass_count += 1
        
        # 薪资要求
        result.salary_met, result.salary_detail = self._check_salary(
            job, candidate
        )
        if not result.salary_met:
            failed_conditions.append("薪资要求")
        else:
            pass_count += 1
        
        # 综合判断
        result.failed_conditions = failed_conditions
        result.all_conditions_met = len(failed_conditions) == 0
        result.pass_score = (pass_count / total_count) * 100
        
        return result
    
    def _check_education(self, job: Job, resume: StructuredResume) -> tuple[bool, str]:
        """检查学历要求"""
        requirements = job.requirements.lower()
        required_education = None
        
        edu_levels = ["博士", "硕士", "本科", "大专", "高中", "中专", "初中"]
        for edu in edu_levels:
            if edu in requirements:
                required_education = edu
                break
        
        if not required_education:
            return True, "无明确学历要求"
        
        resume_edu = resume.highest_degree
        required_idx = edu_levels.index(required_education) if required_education in edu_levels else 0
        
        # 获取简历学历等级
        for edu in edu_levels:
            if edu in resume_edu:
                resume_idx = edu_levels.index(edu)
                if resume_idx >= required_idx:
                    return True, f"满足要求：{resume_edu}"
                else:
                    return False, f"学历不足：要求{required_education}，实际{resume_edu}"
        
        return False, f"学历不足：要求{required_education}"
    
    def _check_experience(self, job: Job, resume: StructuredResume) -> tuple[bool, str]:
        """检查经验要求"""
        requirements = job.requirements
        
        # 提取年限要求
        year_match = re.search(r"(\d+)\s*年", requirements)
        if year_match:
            required_years = int(year_match.group(1))
            if resume.total_years >= required_years:
                return True, f"满足要求：{resume.total_years}年 >= {required_years}年"
            else:
                return False, f"经验不足：要求{required_years}年，实际{resume.total_years}年"
        
        return True, "无明确年限要求"
    
    def _check_skills(self, job: Job, resume: StructuredResume) -> tuple[bool, str]:
        """检查技能要求"""
        requirements = job.requirements.lower()
        
        # 提取必需技能
        required_skills = []
        common_skills = ["python", "java", "sql", "javascript", "react", "vue"]
        for skill in common_skills:
            if skill in requirements:
                required_skills.append(skill)
        
        if not required_skills:
            return True, "无明确技能要求"
        
        matched = [s for s in required_skills if s in resume.hard_skills]
        if len(matched) == len(required_skills):
            return True, f"技能满足：{', '.join(matched)}"
        elif len(matched) >= len(required_skills) * 0.5:
            return True, f"部分满足：{', '.join(matched)}"
        else:
            missing = [s for s in required_skills if s not in resume.hard_skills]
            return False, f"缺少技能：{', '.join(missing)}"
    
    def _check_certification(self, job: Job, resume: StructuredResume) -> tuple[bool, str]:
        """检查证书要求"""
        requirements = job.requirements
        
        # 简单检查
        cert_keywords = ["PMP", "CFA", "CPA", "证书"]
        required = any(kw in requirements for kw in cert_keywords)
        
        if not required:
            return True, "无明确证书要求"
        
        if resume.certifications:
            return True, f"持有证书：{', '.join(resume.certifications)}"
        
        return False, "缺少相关证书"
    
    def _check_location(self, job: Job, candidate: Candidate) -> tuple[bool, str]:
        """检查地点要求"""
        if not job.location:
            return True, "无地点限制"
        
        if candidate.job_intent and "location" in candidate.job_intent:
            preferred = candidate.job_intent["location"]
            if isinstance(preferred, list):
                if job.location in preferred:
                    return True, f"地点匹配：{job.location}"
            elif job.location in preferred:
                return True, f"地点匹配：{job.location}"
        
        if candidate.location and job.location in candidate.location:
            return True, f"地点匹配：{candidate.location}"
        
        return False, f"地点不匹配：要求{job.location}"
    
    def _check_salary(self, job: Job, candidate: Candidate) -> tuple[bool, str]:
        """检查薪资要求"""
        if not job.salary_range:
            return True, "无薪资限制"
        
        if candidate.job_intent and "salary_min" in candidate.job_intent:
            candidate_salary = candidate.job_intent["salary_min"]
            
            # 解析岗位薪资
            salary_match = re.search(r"(\d+)[kK]?-(\d+)[kK]?", job.salary_range)
            if salary_match:
                job_min = int(salary_match.group(1)) * 1000
                job_max = int(salary_match.group(2)) * 1000
                
                if candidate_salary <= job_max:
                    return True, f"薪资符合：{job.salary_range}"
                else:
                    return False, f"薪资不匹配：期望{candidate_salary}，岗位最高{job_max}"
        
        return True, "薪资待确认"


class SemanticMatcher:
    """
    语义匹配引擎
    
    基于NLP技术进行人岗语义匹配。
    """
    
    def match(
        self,
        job: Job,
        candidate: Candidate,
        structured_resume: StructuredResume
    ) -> SemanticMatchResult:
        """
        执行语义匹配
        
        Args:
            job: 岗位实体
            candidate: 候选人实体
            structured_resume: 结构化简历
            
        Returns:
            SemanticMatchResult: 匹配结果
        """
        result = SemanticMatchResult(
            job_id=job.id,
            candidate_id=candidate.id
        )
        
        # 岗位title匹配
        result.title_match_score = self._match_title(job, candidate)
        
        # 技能匹配
        result.skill_match_score = self._match_skills(job, structured_resume)
        
        # 经验匹配
        result.experience_match_score = self._match_experience(job, structured_resume)
        
        # 行业匹配
        result.industry_match_score = self._match_industry(job, candidate)
        
        # 文化匹配
        result.culture_match_score = self._match_culture(job, candidate)
        
        # 综合相似度
        result.overall_similarity = (
            result.title_match_score * 0.20 +
            result.skill_match_score * 0.35 +
            result.experience_match_score * 0.20 +
            result.industry_match_score * 0.15 +
            result.culture_match_score * 0.10
        )
        
        # 匹配分析
        result.matching_skills = list(
            set(job.tags or []) & set(structured_resume.hard_skills or [])
        )
        result.missing_skills = list(
            set(job.tags or []) - set(structured_resume.hard_skills or [])
        )
        result.highlight_experiences = self._extract_highlights(structured_resume)
        
        return result
    
    def _match_title(self, job: Job, candidate: Candidate) -> float:
        """匹配岗位title"""
        job_title = job.title.lower()
        
        # 提取候选人意向职位
        intent_position = ""
        if candidate.job_intent and "position" in candidate.job_intent:
            intent_position = candidate.job_intent["position"].lower()
        
        # 简单关键词匹配
        keywords = job_title.split()
        if intent_position:
            matched = sum(1 for kw in keywords if kw in intent_position)
            return (matched / len(keywords)) * 100 if keywords else 50
        
        return 50.0  # 无法判断时给中等分
    
    def _match_skills(self, job: Job, resume: StructuredResume) -> float:
        """匹配技能"""
        job_skills = set(job.tags or [])
        resume_skills = set(resume.hard_skills or [])
        
        if not job_skills:
            return 70.0  # 无技能要求
        
        matched = job_skills & resume_skills
        return (len(matched) / len(job_skills)) * 100
    
    def _match_experience(self, job: Job, resume: StructuredResume) -> float:
        """匹配经验"""
        requirements = job.requirements
        
        # 提取年限
        year_match = re.search(r"(\d+)\s*年", requirements)
        if year_match:
            required_years = int(year_match.group(1))
            actual_years = resume.total_years
            
            if actual_years >= required_years:
                return min(100, 60 + (actual_years - required_years) * 5)
            else:
                return max(0, (actual_years / required_years) * 60)
        
        # 无年限要求时基于总年限评分
        if resume.total_years >= 5:
            return 80
        elif resume.total_years >= 3:
            return 70
        elif resume.total_years >= 1:
            return 60
        return 40
    
    def _match_industry(self, job: Job, candidate: Candidate) -> float:
        """匹配行业"""
        job_desc = job.description.lower()
        candidate_exp = " ".join([
            exp.get("description", "") for exp in (candidate.job_intent or {}).get("industry", [])
        ]).lower()
        
        if not candidate_exp:
            return 60.0
        
        # 简单行业关键词匹配
        industry_keywords = ["互联网", "金融", "医疗", "教育", "零售", "制造", "咨询"]
        
        job_industries = [kw for kw in industry_keywords if kw in job_desc]
        candidate_industries = [kw for kw in industry_keywords if kw in candidate_exp]
        
        if not job_industries:
            return 70.0
        
        matched = set(job_industries) & set(candidate_industries)
        return (len(matched) / len(job_industries)) * 100
    
    def _match_culture(self, job: Job, candidate: Candidate) -> float:
        """匹配文化"""
        # 简单实现，可扩展
        return 70.0
    
    def _extract_highlights(self, resume: StructuredResume) -> List[str]:
        """提取亮点"""
        highlights = []
        
        # 高学历
        if resume.highest_degree in ["博士", "硕士"]:
            highlights.append(f"{resume.highest_degree}学历")
        
        # 大厂经验
        big_companies = ["腾讯", "阿里", "百度", "字节", "美团", "京东", "华为"]
        for exp in resume.work_experience:
            company = exp.get("company", "")
            if any(bc in company for bc in big_companies):
                highlights.append(f"大厂经验：{company}")
                break
        
        # 丰富项目
        if len(resume.projects) >= 3:
            highlights.append(f"{len(resume.projects)}个项目经验")
        
        # 证书
        if resume.certifications:
            highlights.append(f"持有证书：{', '.join(resume.certifications[:2])}")
        
        return highlights[:5]


class InitialScreeningAgent:
    """
    初筛Agent
    
    整合简历解析、硬性条件过滤和语义匹配，完成简历初筛。
    """
    
    def __init__(self):
        self.resume_parser = ResumeParser()
        self.hard_filter = HardConditionFilterEngine()
        self.semantic_matcher = SemanticMatcher()
    
    async def screen(
        self,
        candidate: Candidate,
        job: Job,
        evaluation_id: str
    ) -> InitialScreeningResult:
        """
        执行初筛
        
        Args:
            candidate: 候选人实体
            job: 岗位实体
            evaluation_id: 评价ID
            
        Returns:
            InitialScreeningResult: 初筛结果
        """
        # 解析简历
        structured_resume = self.resume_parser.parse(
            candidate.resume_text or "",
            candidate.id
        )
        
        # 硬性条件过滤
        hard_filter_result = self.hard_filter.filter(job, candidate, structured_resume)
        
        # 语义匹配
        semantic_result = self.semantic_matcher.match(job, candidate, structured_resume)
        
        # 计算综合初筛得分
        screening_score = self._calculate_screening_score(
            hard_filter_result,
            semantic_result
        )
        
        # 生成建议
        recommendations, concerns = self._generate_feedback(
            hard_filter_result,
            semantic_result
        )
        
        return InitialScreeningResult(
            candidate_id=candidate.id,
            job_id=job.id,
            evaluation_id=evaluation_id,
            structured_resume=structured_resume,
            hard_condition_filter=hard_filter_result,
            semantic_match=semantic_result,
            screening_score=screening_score,
            screening_passed=hard_filter_result.all_conditions_met,
            recommendations=recommendations,
            concerns=concerns
        )
    
    def _calculate_screening_score(
        self,
        hard_filter: HardConditionFilter,
        semantic: SemanticMatchResult
    ) -> float:
        """计算综合初筛得分"""
        hard_weight = 0.4
        semantic_weight = 0.6
        
        hard_score = hard_filter.pass_score
        semantic_score = semantic.overall_similarity
        
        return hard_score * hard_weight + semantic_score * semantic_weight
    
    def _generate_feedback(
        self,
        hard_filter: HardConditionFilter,
        semantic: SemanticMatchResult
    ) -> tuple[List[str], List[str]]:
        """生成反馈"""
        recommendations = []
        concerns = []
        
        if hard_filter.all_conditions_met:
            recommendations.append("满足所有硬性条件")
        else:
            concerns.append(f"未满足条件：{', '.join(hard_filter.failed_conditions)}")
        
        if semantic.skill_match_score >= 80:
            recommendations.append("技能匹配度优秀")
        elif semantic.skill_match_score < 50:
            concerns.append("技能匹配度不足")
        
        if semantic.experience_match_score >= 80:
            recommendations.append("经验匹配度优秀")
        
        if semantic.highlight_experiences:
            recommendations.append(f"亮点：{semantic.highlight_experiences[0]}")
        
        return recommendations, concerns


class DeepAssessmentAgent:
    """
    深度评估Agent
    
    基于冰山模型和STAR框架进行软素质评估。
    """
    
    # 各维度权重
    ICEBERG_WEIGHTS = {
        IcebergDimension.KNOWLEDGE: 0.15,
        IcebergDimension.SKILLS: 0.20,
        IcebergDimension.SELF_KNOWLEDGE: 0.15,
        IcebergDimension.TRAITS: 0.20,
        IcebergDimension.MOTIVES: 0.15,
        IcebergDimension.VALUES: 0.15,
    }
    
    def assess(
        self,
        candidate: Candidate,
        job: Job,
        structured_resume: StructuredResume,
        evaluation_id: str
    ) -> DeepAssessmentResult:
        """
        执行深度评估
        
        Args:
            candidate: 候选人实体
            job: 岗位实体
            structured_resume: 结构化简历
            evaluation_id: 评价ID
            
        Returns:
            DeepAssessmentResult: 深度评估结果
        """
        # 生成面试问题
        questions = self._generate_interview_questions(job, structured_resume)
        
        # 评估软素质
        soft_scores = self._assess_soft_quality(
            candidate, job, structured_resume, questions
        )
        
        # 计算综合软素质得分
        overall_soft_score = self._calculate_overall_soft_score(soft_scores)
        
        # 评估文化匹配和成长潜力
        culture_fit_score = self._assess_culture_fit(candidate, job)
        growth_potential = self._assess_growth_potential(structured_resume)
        
        # 综合评估得分
        assessment_score = (
            overall_soft_score * 0.5 +
            culture_fit_score * 0.25 +
            growth_potential * 0.25
        )
        
        # 提取洞察
        key_strengths, development_areas, risk_indicators = self._extract_insights(
            soft_scores, culture_fit_score, growth_potential
        )
        
        return DeepAssessmentResult(
            candidate_id=candidate.id,
            job_id=job.id,
            evaluation_id=evaluation_id,
            interview_questions=questions,
            soft_quality_scores=soft_scores,
            star_responses=[],  # 面试回答在后续添加
            overall_soft_score=overall_soft_score,
            culture_fit_score=culture_fit_score,
            growth_potential_score=growth_potential,
            assessment_score=assessment_score,
            key_strengths=key_strengths,
            development_areas=development_areas,
            risk_indicators=risk_indicators
        )
    
    def _generate_interview_questions(
        self,
        job: Job,
        resume: StructuredResume
    ) -> List[InterviewQuestion]:
        """生成面试问题"""
        questions = []
        
        # 基于冰山模型生成各维度问题
        question_templates = {
            IcebergDimension.SELF_KNOWLEDGE: [
                "请描述您最大的优点和缺点是什么？",
                "您认为自己最擅长的是什么？",
                "您希望在未来3-5年内达到什么职业目标？"
            ],
            IcebergDimension.TRAITS: [
                "您如何描述自己的性格特点？",
                "在压力下您通常如何应对？",
                "您是偏内向还是外向的人？"
            ],
            IcebergDimension.MOTIVES: [
                "您选择这份工作的主要原因是什么？",
                "什么样的工作环境能让您发挥最大潜力？",
                "您最看重的公司文化是什么？"
            ],
            IcebergDimension.VALUES: [
                "您认同什么样的价值观？",
                "您如何看待工作中的诚信？",
                "什么对您来说最重要？"
            ],
            IcebergDimension.SKILLS: [
                "请分享一个您成功解决问题的案例？",
                "您如何提升自己的专业技能？",
                "面对不熟悉的领域，您通常如何学习？"
            ],
            IcebergDimension.KNOWLEDGE: [
                "您对这个行业有什么理解？",
                "您觉得岗位需要哪些核心知识？",
                "您如何保持对行业动态的了解？"
            ]
        }
        
        for dimension, templates in question_templates.items():
            question_id = f"q_{dimension.value}_{uuid.uuid4().hex[:8]}"
            question = InterviewQuestion(
                question_id=question_id,
                dimension=dimension,
                question_text=templates[0],
                question_type="behavioral",
                follow_up_questions=templates[1:3],
                expected_keywords=self._get_expected_keywords(dimension)
            )
            questions.append(question)
        
        return questions
    
    def _get_expected_keywords(self, dimension: IcebergDimension) -> List[str]:
        """获取期望关键词"""
        keywords_map = {
            IcebergDimension.SELF_KNOWLEDGE: ["反思", "成长", "自我认知"],
            IcebergDimension.TRAITS: ["适应", "抗压", "积极"],
            IcebergDimension.MOTIVES: ["成就", "发展", "挑战"],
            IcebergDimension.VALUES: ["责任", "团队", "创新"],
            IcebergDimension.SKILLS: ["分析", "解决", "沟通"],
            IcebergDimension.KNOWLEDGE: ["行业", "专业", "学习"]
        }
        return keywords_map.get(dimension, [])
    
    def _assess_soft_quality(
        self,
        candidate: Candidate,
        job: Job,
        resume: StructuredResume,
        questions: List[InterviewQuestion]
    ) -> List[SoftQualityDimension]:
        """评估软素质"""
        scores = []
        
        for dimension in IcebergDimension:
            # 基于简历和工作要求进行评估
            score, evidence = self._score_dimension(
                dimension, candidate, job, resume
            )
            
            # 添加评估置信度
            confidence = self._calculate_confidence(dimension, resume)
            
            scores.append(SoftQualityDimension(
                dimension=dimension,
                score=score,
                evidence=evidence,
                examples=[],
                confidence=confidence
            ))
        
        return scores
    
    def _score_dimension(
        self,
        dimension: IcebergDimension,
        candidate: Candidate,
        job: Job,
        resume: StructuredResume
    ) -> tuple[float, List[str]]:
        """评分特定维度"""
        score = 50.0
        evidence = []
        
        if dimension == IcebergDimension.KNOWLEDGE:
            # 基于教育背景和行业经历评分
            if resume.highest_degree in ["博士", "硕士"]:
                score += 20
                evidence.append(f"高学历背景：{resume.highest_degree}")
            if resume.major:
                score += 10
                evidence.append(f"专业对口：{resume.major}")
        
        elif dimension == IcebergDimension.SKILLS:
            # 基于技能匹配度评分
            matched_skills = set(resume.hard_skills) & set(job.tags or [])
            if matched_skills:
                score += min(30, len(matched_skills) * 5)
                evidence.append(f"匹配技能：{', '.join(list(matched_skills)[:3])}")
            if resume.soft_skills:
                score += 10
                evidence.append(f"软技能：{', '.join(resume.soft_skills[:2])}")
        
        elif dimension == IcebergDimension.SELF_KNOWLEDGE:
            # 基于自我认知评分
            if resume.projects:
                score += 15
                evidence.append(f"项目经验丰富：{len(resume.projects)}个项目")
            if resume.certifications:
                score += 10
                evidence.append(f"持续学习：{', '.join(resume.certifications[:2])}")
        
        elif dimension == IcebergDimension.TRAITS:
            # 基于稳定性评分
            score += 10
            evidence.append("特质待面试观察")
        
        elif dimension == IcebergDimension.MOTIVES:
            # 基于求职意向清晰度评分
            if candidate.job_intent:
                score += 20
                evidence.append("求职意向清晰")
        
        elif dimension == IcebergDimension.VALUES:
            # 价值观待深入评估
            score += 5
            evidence.append("价值观待面试了解")
        
        return min(score, 100.0), evidence
    
    def _calculate_confidence(self, dimension: IcebergDimension, resume: StructuredResume) -> float:
        """计算评估置信度"""
        base_confidence = 0.5
        
        if dimension == IcebergDimension.KNOWLEDGE:
            if resume.education:
                return 0.8
        elif dimension == IcebergDimension.SKILLS:
            if resume.hard_skills:
                return 0.8
        elif dimension == IcebergDimension.SELF_KNOWLEDGE:
            if resume.projects or resume.certifications:
                return 0.6
        
        return base_confidence
    
    def _calculate_overall_soft_score(self, scores: List[SoftQualityDimension]) -> float:
        """计算综合软素质得分"""
        weighted_sum = 0.0
        total_weight = 0.0
        
        for score in scores:
            weight = self.ICEBERG_WEIGHTS.get(score.dimension, 0.1)
            weighted_sum += score.score * weight * score.confidence
            total_weight += weight * score.confidence
        
        if total_weight == 0:
            return 50.0
        
        return weighted_sum / total_weight
    
    def _assess_culture_fit(self, candidate: Candidate, job: Job) -> float:
        """评估文化匹配度"""
        score = 70.0
        
        # 基于地点匹配
        if candidate.location and job.location:
            if candidate.location in job.location or job.location in candidate.location:
                score += 10
        
        # 基于求职意向
        if candidate.job_intent:
            if "job_type" in candidate.job_intent:
                score += 10
            if "location" in candidate.job_intent:
                score += 10
        
        return min(score, 100.0)
    
    def _assess_growth_potential(self, resume: StructuredResume) -> float:
        """评估成长潜力"""
        score = 60.0
        
        # 学历加成
        if resume.highest_degree in ["博士", "硕士"]:
            score += 15
        elif resume.highest_degree == "本科":
            score += 10
        
        # 持续学习
        if resume.certifications:
            score += 10
        
        # 年龄与经验平衡
        if resume.age and resume.age < 35:
            score += 10
        
        # 项目经验
        if len(resume.projects) >= 3:
            score += 5
        
        return min(score, 100.0)
    
    def _extract_insights(
        self,
        soft_scores: List[SoftQualityDimension],
        culture_fit: float,
        growth: float
    ) -> tuple[List[str], List[str], List[str]]:
        """提取洞察"""
        strengths = []
        development = []
        risks = []
        
        for score in soft_scores:
            if score.score >= 75:
                strengths.append(f"{score.dimension.value}能力强")
            elif score.score < 50:
                development.append(f"{score.dimension.value}需提升")
        
        if culture_fit >= 80:
            strengths.append("文化匹配度高")
        elif culture_fit < 60:
            risks.append("文化匹配度可能存在问题")
        
        if growth >= 80:
            strengths.append("成长潜力大")
        elif growth < 50:
            risks.append("成长潜力有限")
        
        return strengths[:5], development[:5], risks[:3]


class CandidateEvaluationService:
    """
    候选人评价服务
    
    整合初筛Agent和深度评估Agent，完成候选人的完整评价。
    """
    
    def __init__(
        self,
        candidate_repo: CandidateRepository,
        job_repo: JobRepository,
        evaluation_repo: CandidateEvaluationRepository
    ):
        """
        初始化候选人评价服务
        
        Args:
            candidate_repo: 候选人仓储
            job_repo: 岗位仓储
            evaluation_repo: 候选人评价仓储
        """
        self.candidate_repo = candidate_repo
        self.job_repo = job_repo
        self.evaluation_repo = evaluation_repo
        self.initial_screening_agent = InitialScreeningAgent()
        self.deep_assessment_agent = DeepAssessmentAgent()
    
    async def evaluate_candidate(
        self,
        candidate_id: str,
        job_id: str,
        perform_deep_assessment: bool = True
    ) -> CandidateEvaluation:
        """
        执行候选人综合评价
        
        Args:
            candidate_id: 候选人ID
            job_id: 岗位ID
            perform_deep_assessment: 是否执行深度评估
            
        Returns:
            CandidateEvaluation: 综合评价结果
        """
        # 获取候选人和岗位
        candidate = await self.candidate_repo.get_by_id(candidate_id)
        job = await self.job_repo.get_by_id(job_id)
        
        if not candidate or not job:
            raise ValueError("Candidate or Job not found")
        
        evaluation_id = str(uuid.uuid4())
        evaluation = CandidateEvaluation(
            candidate_id=candidate_id,
            job_id=job_id,
            evaluation_id=evaluation_id,
            current_stage=EvaluationStage.INITIAL_SCREENING
        )
        
        # 初筛阶段
        screening_result = await self.initial_screening_agent.screen(
            candidate, job, evaluation_id
        )
        evaluation.initial_screening = screening_result
        evaluation.current_stage = EvaluationStage.INITIAL_SCREENING
        
        # 深度评估阶段
        if perform_deep_assessment and screening_result.screening_passed:
            assessment_result = self.deep_assessment_agent.assess(
                candidate, job, screening_result.structured_resume, evaluation_id
            )
            evaluation.deep_assessment = assessment_result
            evaluation.current_stage = EvaluationStage.DEEP_ASSESSMENT
            
            # 计算最终得分
            evaluation.final_score = self._calculate_final_score(
                screening_result.screening_score,
                assessment_result.assessment_score
            )
            
            # 生成决策建议
            evaluation.evaluation_level, evaluation.recommendation, evaluation.decision_reasons = \
                self._generate_decision(screening_result, assessment_result)
            
            evaluation.evaluation_summary = self._generate_summary(evaluation)
            evaluation.current_stage = EvaluationStage.FINAL_REPORT
        else:
            evaluation.final_score = screening_result.screening_score
            if not screening_result.screening_passed:
                evaluation.evaluation_level = "D"
                evaluation.recommendation = "reject"
                evaluation.decision_reasons = screening_result.concerns
        
        # 保存评价
        await self.evaluation_repo.save(evaluation)
        
        # 保存初筛和评估结果
        await self.evaluation_repo.save_initial_screening(screening_result)
        if evaluation.deep_assessment:
            await self.evaluation_repo.save_deep_assessment(evaluation.deep_assessment)
        
        return evaluation
    
    def _calculate_final_score(
        self,
        screening_score: float,
        assessment_score: float
    ) -> float:
        """计算最终综合得分"""
        return (
            screening_score * 0.4 +
            assessment_score * 0.6
        )
    
    def _generate_decision(
        self,
        screening: InitialScreeningResult,
        assessment: DeepAssessmentResult
    ) -> tuple[str, str, List[str]]:
        """生成决策建议"""
        final_score = (
            screening.screening_score * 0.4 +
            assessment.assessment_score * 0.6
        )
        
        reasons = []
        
        if final_score >= 85:
            level = "A"
            decision = "strong_buy"
            reasons.append("综合评价优秀")
        elif final_score >= 70:
            level = "B"
            decision = "buy"
            reasons.append("综合评价良好")
        elif final_score >= 55:
            level = "C"
            decision = "hold"
            reasons.append("综合评价一般，需要进一步了解")
        else:
            level = "D"
            decision = "reject"
            reasons.append("综合评价不满足要求")
        
        # 添加具体原因
        reasons.extend(screening.recommendations[:2])
        reasons.extend(assessment.key_strengths[:2])
        
        if assessment.risk_indicators:
            reasons.append(f"风险提示：{assessment.risk_indicators[0]}")
        
        return level, decision, reasons
    
    def _generate_summary(self, evaluation: CandidateEvaluation) -> str:
        """生成评价摘要"""
        level_map = {"A": "强烈推荐", "B": "推荐", "C": "待定", "D": "不推荐"}
        level_text = level_map.get(evaluation.evaluation_level, "未知")
        
        summary = f"候选人在本岗位的综合评价为{level_text}，"
        summary += f"最终得分{evaluation.final_score:.1f}分。"
        
        if evaluation.evaluation_level in ["A", "B"]:
            summary += "建议进入下一轮面试。"
        elif evaluation.evaluation_level == "C":
            summary += "建议与用人部门确认具体要求。"
        else:
            summary += "建议寻找更匹配的候选人。"
        
        return summary
    
    async def get_evaluation(self, evaluation_id: str) -> Optional[CandidateEvaluation]:
        """
        获取评价结果
        
        Args:
            evaluation_id: 评价ID
            
        Returns:
            Optional[CandidateEvaluation]: 评价结果
        """
        return await self.evaluation_repo.get_by_id(evaluation_id)
    
    async def generate_report(self, evaluation_id: str) -> Optional[CandidateEvaluationReport]:
        """
        生成评价报告
        
        Args:
            evaluation_id: 评价ID
            
        Returns:
            Optional[CandidateEvaluationReport]: 评价报告
        """
        evaluation = await self.evaluation_repo.get_by_id(evaluation_id)
        if not evaluation:
            return None
        
        # 生成报告内容
        summary = self._generate_report_summary(evaluation)
        highlights = self._extract_highlights(evaluation)
        concerns = self._extract_concerns(evaluation)
        job_fit = self._analyze_job_fit(evaluation)
        risks = self._assess_risks(evaluation)
        
        return CandidateEvaluationReport(
            candidate_evaluation=evaluation,
            executive_summary=summary,
            highlights=highlights,
            concerns=concerns,
            job_fit_analysis=job_fit,
            risk_assessment=risks
        )
    
    def _generate_report_summary(self, evaluation: CandidateEvaluation) -> str:
        """生成报告摘要"""
        level_map = {"A": "强烈推荐", "B": "推荐", "C": "待定", "D": "不推荐"}
        return evaluation.evaluation_summary or f"综合评价{level_map.get(evaluation.evaluation_level, '未知')}"
    
    def _extract_highlights(self, evaluation: CandidateEvaluation) -> List[str]:
        """提取亮点"""
        highlights = []
        
        if evaluation.initial_screening:
            highlights.extend(evaluation.initial_screening.recommendations[:3])
        
        if evaluation.deep_assessment:
            highlights.extend(evaluation.deep_assessment.key_strengths[:3])
        
        return highlights[:5]
    
    def _extract_concerns(self, evaluation: CandidateEvaluation) -> List[str]:
        """提取关注点"""
        concerns = []
        
        if evaluation.initial_screening:
            concerns.extend(evaluation.initial_screening.concerns[:3])
        
        if evaluation.deep_assessment:
            concerns.extend(evaluation.deep_assessment.development_areas[:3])
        
        return concerns[:5]
    
    def _analyze_job_fit(self, evaluation: CandidateEvaluation) -> Dict[str, Any]:
        """分析人岗匹配"""
        if evaluation.initial_screening and evaluation.initial_screening.semantic_match:
            semantic = evaluation.initial_screening.semantic_match
            return {
                "overall_fit_score": semantic.overall_similarity,
                "skill_match": semantic.skill_match_score,
                "experience_match": semantic.experience_match_score,
                "matching_skills": semantic.matching_skills,
                "missing_skills": semantic.missing_skills
            }
        return {}
    
    def _assess_risks(self, evaluation: CandidateEvaluation) -> Dict[str, float]:
        """评估风险"""
        risks = {}
        
        if evaluation.initial_screening:
            if not evaluation.initial_screening.screening_passed:
                risks["screening_fail"] = 1.0
            if evaluation.initial_screening.hard_condition_filter:
                risks["hard_condition_fail"] = 1.0 - (
                    evaluation.initial_screening.hard_condition_filter.pass_score / 100
                )
        
        if evaluation.deep_assessment:
            risks["culture_fit"] = 1.0 - (evaluation.deep_assessment.culture_fit_score / 100)
            risks["growth_potential"] = 1.0 - (evaluation.deep_assessment.growth_potential_score / 100)
        
        return risks
