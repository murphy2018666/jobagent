from typing import List, Dict, Any, Tuple
from loguru import logger
from ..domain.entities import Job, Candidate, Match
from ..domain.repositories import JobRepository, CandidateRepository, MatchRepository
from ..domain.services import MatchingService, WeightConfig
from ..config.settings import settings


class MatchingServiceImpl(MatchingService):
    """
    匹配引擎服务实现
    
    基于多维度评分算法实现岗位与候选人的智能匹配，支持技能匹配、经验匹配、学历匹配、地点匹配和薪资匹配。
    """
    
    def __init__(
        self,
        job_repo: JobRepository,
        candidate_repo: CandidateRepository,
        match_repo: MatchRepository,
    ):
        """
        初始化匹配引擎服务
        
        Args:
            job_repo: 岗位仓储实例
            candidate_repo: 候选人仓储实例
            match_repo: 匹配仓储实例
        """
        self.job_repo = job_repo
        self.candidate_repo = candidate_repo
        self.match_repo = match_repo

    async def build_job_profile(self, job: Job) -> Dict[str, Any]:
        """
        构建岗位画像
        
        从岗位实体中提取关键信息，构建用于匹配的岗位画像。
        
        Args:
            job: 岗位实体
            
        Returns:
            Dict[str, Any]: 岗位画像字典
        """
        return {
            "title": job.title,
            "description": job.description,
            "requirements": job.requirements,
            "location": job.location,
            "salary_range": job.salary_range,
            "tags": job.tags,
            "skills": self._extract_skills(job.requirements),
        }

    async def build_candidate_profile(self, candidate: Candidate) -> Dict[str, Any]:
        """
        构建候选人画像
        
        从候选人实体中提取关键信息，构建用于匹配的候选人画像。
        
        Args:
            candidate: 候选人实体
            
        Returns:
            Dict[str, Any]: 候选人画像字典
        """
        return {
            "name": candidate.name,
            "skills": candidate.skills,
            "experience": candidate.experience,
            "education": candidate.education,
            "job_intent": candidate.job_intent,
            "location_preference": candidate.job_intent.get("location", []),
            "salary_expectation": candidate.job_intent.get("salary_min", 0),
        }

    async def calculate_match_score(self, job_profile: Dict[str, Any], candidate_profile: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        计算匹配分数
        
        根据岗位画像和候选人画像计算综合匹配分数，包含技能、经验、学历、地点和薪资五个维度。
        
        Args:
            job_profile: 岗位画像
            candidate_profile: 候选人画像
            
        Returns:
            Tuple[float, List[str]]: 匹配分数（0-1）和匹配理由列表
        """
        score = 0.0
        reasons = []

        skills_score, skills_reasons = self._calculate_skills_score(job_profile, candidate_profile)
        score += skills_score * WeightConfig.SKILLS_WEIGHT
        reasons.extend(skills_reasons)

        exp_score, exp_reasons = self._calculate_experience_score(job_profile, candidate_profile)
        score += exp_score * WeightConfig.EXPERIENCE_WEIGHT
        reasons.extend(exp_reasons)

        edu_score, edu_reasons = self._calculate_education_score(job_profile, candidate_profile)
        score += edu_score * WeightConfig.EDUCATION_WEIGHT
        reasons.extend(edu_reasons)

        loc_score, loc_reasons = self._calculate_location_score(job_profile, candidate_profile)
        score += loc_score * WeightConfig.LOCATION_WEIGHT
        reasons.extend(loc_reasons)

        sal_score, sal_reasons = self._calculate_salary_score(job_profile, candidate_profile)
        score += sal_score * WeightConfig.SALARY_WEIGHT
        reasons.extend(sal_reasons)

        return min(score, 1.0), reasons[:5]

    async def match_job_with_candidates(self, job_id: str, top_n: int = 10) -> List[Match]:
        """
        岗位匹配候选人
        
        根据岗位ID查找最匹配的候选人，并保存匹配记录。
        
        Args:
            job_id: 岗位ID
            top_n: 返回前N个匹配结果，默认为10
            
        Returns:
            List[Match]: 匹配结果列表，按匹配分数降序排列
        """
        job = await self.job_repo.get_by_id(job_id)
        if not job:
            return []

        job_profile = await self.build_job_profile(job)
        candidates = await self.candidate_repo.search({})
        
        matches = []
        for candidate in candidates:
            candidate_profile = await self.build_candidate_profile(candidate)
            score, reasons = await self.calculate_match_score(job_profile, candidate_profile)
            
            if score >= settings.MATCH_SCORE_THRESHOLD:
                match = Match(
                    job_id=job_id,
                    candidate_id=candidate.id,
                    score=score,
                    match_reasons=reasons,
                )
                matches.append(match)

        matches.sort(key=lambda m: m.score, reverse=True)
        top_matches = matches[:top_n]

        for match in top_matches:
            await self.match_repo.save(match)

        return top_matches

    async def match_candidate_with_jobs(self, candidate_id: str, top_n: int = 10) -> List[Match]:
        """
        候选人匹配岗位
        
        根据候选人ID查找最匹配的开放岗位，并保存匹配记录。
        
        Args:
            candidate_id: 候选人ID
            top_n: 返回前N个匹配结果，默认为10
            
        Returns:
            List[Match]: 匹配结果列表，按匹配分数降序排列
        """
        candidate = await self.candidate_repo.get_by_id(candidate_id)
        if not candidate:
            return []

        candidate_profile = await self.build_candidate_profile(candidate)
        jobs = await self.job_repo.search({})
        
        matches = []
        for job in jobs:
            if not job.is_open():
                continue
            
            job_profile = await self.build_job_profile(job)
            score, reasons = await self.calculate_match_score(job_profile, candidate_profile)
            
            if score >= settings.MATCH_SCORE_THRESHOLD:
                match = Match(
                    job_id=job.id,
                    candidate_id=candidate_id,
                    score=score,
                    match_reasons=reasons,
                )
                matches.append(match)

        matches.sort(key=lambda m: m.score, reverse=True)
        top_matches = matches[:top_n]

        for match in top_matches:
            await self.match_repo.save(match)

        return top_matches

    def _extract_skills(self, text: str) -> List[str]:
        """
        从文本中提取技能
        
        根据预定义的常见技能列表，从文本中提取匹配的技能。
        
        Args:
            text: 待分析的文本
            
        Returns:
            List[str]: 提取到的技能列表
        """
        common_skills = ["python", "java", "javascript", "sql", "react", "vue", "docker", "aws"]
        skills = []
        for skill in common_skills:
            if skill.lower() in text.lower():
                skills.append(skill)
        return skills

    def _calculate_skills_score(self, job: Dict[str, Any], candidate: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        计算技能匹配分数
        
        比较岗位要求的技能和候选人具备的技能，计算匹配度。
        
        Args:
            job: 岗位画像
            candidate: 候选人画像
            
        Returns:
            Tuple[float, List[str]]: 技能匹配分数（0-1）和匹配理由
        """
        job_skills = set(job.get("skills", []) + job.get("tags", []))
        candidate_skills = set(candidate.get("skills", []))
        
        if not job_skills:
            return 0.5, ["技能要求不明确"]
        
        matched = job_skills & candidate_skills
        score = len(matched) / len(job_skills)
        
        reasons = []
        if matched:
            reasons.append(f"匹配技能: {', '.join(matched)}")
        if job_skills - matched:
            reasons.append(f"缺少技能: {', '.join(job_skills - matched)}")
        
        return score, reasons

    def _calculate_experience_score(self, job: Dict[str, Any], candidate: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        计算经验匹配分数
        
        比较岗位要求的工作经验年限和候选人的经验年限。
        
        Args:
            job: 岗位画像
            candidate: 候选人画像
            
        Returns:
            Tuple[float, List[str]]: 经验匹配分数（0-1）和匹配理由
        """
        job_requirements = job.get("requirements", "")
        candidate_exp = candidate.get("experience", "")
        
        job_years = self._extract_years(job_requirements)
        candidate_years = self._extract_years(candidate_exp)
        
        if job_years == 0:
            return 0.7, ["经验要求不明确"]
        
        if candidate_years >= job_years:
            return 1.0, [f"经验符合要求: {candidate_years}年 >= {job_years}年"]
        elif candidate_years >= job_years * 0.5:
            return 0.7, [f"经验接近要求: {candidate_years}年 / {job_years}年"]
        else:
            return 0.3, [f"经验不足: {candidate_years}年 < {job_years}年"]

    def _extract_years(self, text: str) -> int:
        """
        从文本中提取年限
        
        使用正则表达式从文本中提取工作经验年限。
        
        Args:
            text: 待分析的文本
            
        Returns:
            int: 提取到的年限，未找到返回0
        """
        import re
        match = re.search(r"(\d+)\s*年", text)
        if match:
            return int(match.group(1))
        match = re.search(r"(\d+)\-(\d+)\s*年", text)
        if match:
            return int(match.group(1))
        return 0

    def _calculate_education_score(self, job: Dict[str, Any], candidate: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        计算学历匹配分数
        
        比较岗位要求的学历和候选人的学历。
        
        Args:
            job: 岗位画像
            candidate: 候选人画像
            
        Returns:
            Tuple[float, List[str]]: 学历匹配分数（0-1）和匹配理由
        """
        edu_levels = {"初中": 1, "高中": 2, "大专": 3, "本科": 4, "硕士": 5, "博士": 6}
        
        job_requirements = job.get("requirements", "")
        candidate_edu = candidate.get("education", "")
        
        job_edu = self._extract_education(job_requirements)
        candidate_edu_level = edu_levels.get(candidate_edu, 0)
        job_edu_level = edu_levels.get(job_edu, 0)
        
        if job_edu_level == 0:
            return 0.8, ["学历要求不明确"]
        
        if candidate_edu_level >= job_edu_level:
            return 1.0, [f"学历符合要求: {candidate_edu} >= {job_edu}"]
        else:
            return 0.4, [f"学历不足: {candidate_edu} < {job_edu}"]

    def _extract_education(self, text: str) -> str:
        """
        从文本中提取学历
        
        根据预定义的学历关键字列表，从文本中提取匹配的学历。
        
        Args:
            text: 待分析的文本
            
        Returns:
            str: 提取到的学历，未找到返回空字符串
        """
        edu_keywords = ["博士", "硕士", "本科", "大专", "高中", "初中"]
        for edu in edu_keywords:
            if edu in text:
                return edu
        return ""

    def _calculate_location_score(self, job: Dict[str, Any], candidate: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        计算地点匹配分数
        
        比较岗位工作地点和候选人的地点偏好。
        
        Args:
            job: 岗位画像
            candidate: 候选人画像
            
        Returns:
            Tuple[float, List[str]]: 地点匹配分数（0-1）和匹配理由
        """
        job_location = job.get("location", "")
        candidate_locations = candidate.get("location_preference", [])
        
        if not job_location:
            return 0.8, ["工作地点未指定"]
        
        if job_location in candidate_locations:
            return 1.0, [f"地点匹配: {job_location}"]
        elif len(candidate_locations) == 0:
            return 0.7, ["候选人无地点限制"]
        else:
            return 0.5, [f"地点不匹配: {job_location} vs {candidate_locations}"]

    def _calculate_salary_score(self, job: Dict[str, Any], candidate: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        计算薪资匹配分数
        
        比较岗位薪资范围和候选人的薪资期望。
        
        Args:
            job: 岗位画像
            candidate: 候选人画像
            
        Returns:
            Tuple[float, List[str]]: 薪资匹配分数（0-1）和匹配理由
        """
        job_salary = job.get("salary_range", "")
        candidate_salary_min = candidate.get("salary_expectation", 0)
        
        if not job_salary or candidate_salary_min == 0:
            return 0.7, ["薪资信息不完整"]
        
        min_sal, max_sal = self._parse_salary_range(job_salary)
        
        if candidate_salary_min <= max_sal:
            return 1.0, [f"薪资符合期望: {job_salary}"]
        else:
            return 0.4, [f"薪资低于期望: {job_salary} < {candidate_salary_min}"]

    def _parse_salary_range(self, salary_range: str) -> Tuple[int, int]:
        """
        解析薪资范围
        
        从字符串中解析薪资范围，支持如"10k-20k"或"15k"格式。
        
        Args:
            salary_range: 薪资范围字符串
            
        Returns:
            Tuple[int, int]: 最低薪资和最高薪资（单位：元）
        """
        import re
        match = re.search(r"(\d+)[kK]?[\s-]*(\d+)?[kK]?", salary_range)
        if match:
            min_sal = int(match.group(1)) * 1000
            max_sal = int(match.group(2)) * 1000 if match.group(2) else min_sal * 2
            return min_sal, max_sal
        return 0, 0
