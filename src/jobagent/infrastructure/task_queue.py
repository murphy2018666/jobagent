from celery import Celery
from celery.schedules import crontab
from typing import Any, Dict, Callable
from loguru import logger
from ..config.settings import settings


celery = Celery(
    "jobagent",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=240,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)


@celery.task(bind=True, retry_backoff=True, retry_backoff_max=300)
def async_match_job(self, job_id: str, top_n: int = 10) -> Dict[str, Any]:
    """
    异步匹配岗位与候选人
    
    根据岗位ID查找最匹配的候选人，使用延迟导入避免循环依赖。
    
    Args:
        self: Celery任务实例
        job_id: 岗位ID
        top_n: 返回前N个匹配结果，默认为10
        
    Returns:
        Dict[str, Any]: 任务执行结果，包含状态、岗位ID和匹配数量
        
    Raises:
        Exception: 匹配过程中发生错误时自动重试
    """
    try:
        from ..application.services import MatchApplicationService
        from ..application.commands import MatchJobCommand
        
        match_service = MatchApplicationService()
        results = match_service.match_job_with_candidates(
            MatchJobCommand(job_id=job_id, top_n=top_n)
        )
        logger.info(f"Async match job {job_id} completed, found {len(results)} matches")
        return {"status": "success", "job_id": job_id, "match_count": len(results)}
    except Exception as e:
        logger.error(f"Async match job {job_id} failed: {str(e)}")
        raise self.retry(exc=e, max_retries=3)


@celery.task(bind=True, retry_backoff=True, retry_backoff_max=300)
def async_match_candidate(self, candidate_id: str, top_n: int = 10) -> Dict[str, Any]:
    """
    异步匹配候选人与岗位
    
    根据候选人ID查找最匹配的岗位，使用延迟导入避免循环依赖。
    
    Args:
        self: Celery任务实例
        candidate_id: 候选人ID
        top_n: 返回前N个匹配结果，默认为10
        
    Returns:
        Dict[str, Any]: 任务执行结果，包含状态、候选人ID和匹配数量
        
    Raises:
        Exception: 匹配过程中发生错误时自动重试
    """
    try:
        from ..application.services import MatchApplicationService
        from ..application.commands import MatchCandidateCommand
        
        match_service = MatchApplicationService()
        results = match_service.match_candidate_with_jobs(
            MatchCandidateCommand(candidate_id=candidate_id, top_n=top_n)
        )
        logger.info(f"Async match candidate {candidate_id} completed, found {len(results)} matches")
        return {"status": "success", "candidate_id": candidate_id, "match_count": len(results)}
    except Exception as e:
        logger.error(f"Async match candidate {candidate_id} failed: {str(e)}")
        raise self.retry(exc=e, max_retries=3)


@celery.task(bind=True)
def sync_company_jobs(self, company_id: str) -> Dict[str, Any]:
    """
    同步企业岗位数据
    
    从企业的MCP服务器同步最新的岗位信息，使用延迟导入避免循环依赖。
    
    Args:
        self: Celery任务实例
        company_id: 企业ID
        
    Returns:
        Dict[str, Any]: 任务执行结果，包含状态、企业ID和同步的岗位数量
        
    Raises:
        Exception: 同步过程中发生错误时自动重试
    """
    try:
        from ..application.services import JobApplicationService
        
        job_service = JobApplicationService()
        jobs = job_service.sync_jobs_from_mcp(company_id)
        logger.info(f"Sync company {company_id} jobs completed, {len(jobs)} jobs synced")
        return {"status": "success", "company_id": company_id, "job_count": len(jobs)}
    except Exception as e:
        logger.error(f"Sync company {company_id} jobs failed: {str(e)}")
        raise self.retry(exc=e, max_retries=3)


@celery.task(bind=True)
def fetch_candidate_profile(self, candidate_id: str) -> Dict[str, Any]:
    """
    获取候选人最新简历
    
    从候选人的MCP服务器获取最新的简历信息，使用延迟导入避免循环依赖。
    
    Args:
        self: Celery任务实例
        candidate_id: 候选人ID
        
    Returns:
        Dict[str, Any]: 任务执行结果，包含状态和候选人ID
        
    Raises:
        Exception: 获取过程中发生错误时自动重试
    """
    try:
        from ..application.services import CandidateApplicationService
        
        candidate_service = CandidateApplicationService()
        profile = candidate_service.fetch_profile_from_mcp(candidate_id)
        logger.info(f"Fetch candidate {candidate_id} profile completed")
        return {"status": "success", "candidate_id": candidate_id}
    except Exception as e:
        logger.error(f"Fetch candidate {candidate_id} profile failed: {str(e)}")
        raise self.retry(exc=e, max_retries=3)


@celery.task(bind=True)
def notify_company(self, match_id: str, event_type: str) -> Dict[str, Any]:
    """
    通知企业相关事件
    
    向企业发送匹配相关的通知消息，使用延迟导入避免循环依赖。
    
    Args:
        self: Celery任务实例
        match_id: 匹配记录ID
        event_type: 事件类型
        
    Returns:
        Dict[str, Any]: 任务执行结果，包含状态、匹配ID和事件类型
        
    Raises:
        Exception: 通知过程中发生错误时自动重试
    """
    try:
        from ..application.services import ProcessApplicationService
        
        process_service = ProcessApplicationService()
        process_service.notify_company(match_id)
        logger.info(f"Notify company for match {match_id}, event: {event_type}")
        return {"status": "success", "match_id": match_id, "event_type": event_type}
    except Exception as e:
        logger.error(f"Notify company for match {match_id} failed: {str(e)}")
        raise self.retry(exc=e, max_retries=2)


@celery.task(bind=True)
def notify_candidate(self, match_id: str, event_type: str) -> Dict[str, Any]:
    """
    通知候选人相关事件
    
    向候选人发送匹配相关的通知消息，使用延迟导入避免循环依赖。
    
    Args:
        self: Celery任务实例
        match_id: 匹配记录ID
        event_type: 事件类型
        
    Returns:
        Dict[str, Any]: 任务执行结果，包含状态、匹配ID和事件类型
        
    Raises:
        Exception: 通知过程中发生错误时自动重试
    """
    try:
        from ..application.services import ProcessApplicationService
        
        process_service = ProcessApplicationService()
        process_service.notify_candidate(match_id)
        logger.info(f"Notify candidate for match {match_id}, event: {event_type}")
        return {"status": "success", "match_id": match_id, "event_type": event_type}
    except Exception as e:
        logger.error(f"Notify candidate for match {match_id} failed: {str(e)}")
        raise self.retry(exc=e, max_retries=2)


@celery.task
def cleanup_expired_matches():
    """
    清理过期的匹配记录
    
    删除30天前创建且仍处于待处理状态的匹配记录，用于定期清理数据库。
    
    Returns:
        Dict[str, Any]: 任务执行结果，包含状态
        
    Raises:
        Exception: 清理过程中发生错误时抛出异常
    """
    try:
        from datetime import datetime, timedelta
        from ..infrastructure.database import DatabaseMatchRepository, get_session
        from ..domain.entities import MatchStatus
        
        async def cleanup():
            async for session in get_session():
                repo = DatabaseMatchRepository(session)
                cutoff_time = datetime.now() - timedelta(days=30)
                matches = await repo.list_by_status(MatchStatus.PENDING)
                expired_count = 0
                for match in matches:
                    if match.created_at < cutoff_time:
                        await repo.delete(match.id)
                        expired_count += 1
                logger.info(f"Cleanup completed, {expired_count} expired matches removed")
        
        import asyncio
        asyncio.run(cleanup())
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Cleanup expired matches failed: {str(e)}")
        raise


# Celery定时任务配置
celery.conf.beat_schedule = {
    "cleanup-expired-matches": {
        "task": "src.jobagent.infrastructure.task_queue.cleanup_expired_matches",
        "schedule": crontab(hour=3, minute=0),
    },
}


class TaskQueueService:
    """任务队列服务封装"""
    
    @staticmethod
    def submit_match_job(job_id: str, top_n: int = 10) -> str:
        """
        提交岗位匹配任务
        
        Args:
            job_id: 岗位ID
            top_n: 返回前N个匹配结果，默认为10
            
        Returns:
            str: 任务ID
        """
        task = async_match_job.delay(job_id, top_n)
        return task.task_id
    
    @staticmethod
    def submit_match_candidate(candidate_id: str, top_n: int = 10) -> str:
        """
        提交候选人匹配任务
        
        Args:
            candidate_id: 候选人ID
            top_n: 返回前N个匹配结果，默认为10
            
        Returns:
            str: 任务ID
        """
        task = async_match_candidate.delay(candidate_id, top_n)
        return task.task_id
    
    @staticmethod
    def submit_sync_jobs(company_id: str) -> str:
        """
        提交岗位同步任务
        
        Args:
            company_id: 企业ID
            
        Returns:
            str: 任务ID
        """
        task = sync_company_jobs.delay(company_id)
        return task.task_id
    
    @staticmethod
    def submit_fetch_profile(candidate_id: str) -> str:
        """
        提交获取简历任务
        
        Args:
            candidate_id: 候选人ID
            
        Returns:
            str: 任务ID
        """
        task = fetch_candidate_profile.delay(candidate_id)
        return task.task_id
    
    @staticmethod
    def submit_notify_company(match_id: str, event_type: str) -> str:
        """
        提交通知企业任务
        
        Args:
            match_id: 匹配记录ID
            event_type: 事件类型
            
        Returns:
            str: 任务ID
        """
        task = notify_company.delay(match_id, event_type)
        return task.task_id
    
    @staticmethod
    def submit_notify_candidate(match_id: str, event_type: str) -> str:
        """
        提交通知候选人任务
        
        Args:
            match_id: 匹配记录ID
            event_type: 事件类型
            
        Returns:
            str: 任务ID
        """
        task = notify_candidate.delay(match_id, event_type)
        return task.task_id
    
    @staticmethod
    def get_task_status(task_id: str) -> Dict[str, Any]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            Dict[str, Any]: 任务状态信息，包含任务ID、状态、结果和错误信息
        """
        task = async_match_job.AsyncResult(task_id)
        return {
            "task_id": task_id,
            "status": task.status,
            "result": task.result if task.successful() else None,
            "error": str(task.info) if task.failed() else None,
        }
