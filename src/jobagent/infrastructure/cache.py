import redis
from typing import Any, Optional, Dict, List, Callable
import json
from datetime import timedelta
from ..config.settings import settings


class RedisCache:
    """
    Redis缓存服务
    
    基于Redis实现的缓存服务，提供数据的存储、获取、删除等操作，支持过期时间设置和发布订阅功能。
    """
    
    def __init__(self):
        """
        初始化Redis缓存服务
        
        从配置中读取Redis连接URL并创建客户端连接。
        """
        self.client = redis.from_url(settings.REDIS_URL)

    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存数据
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[Any]: 缓存值，如果不存在返回None
        """
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception:
            return None

    async def set(self, key: str, value: Any, expires_in: Optional[timedelta] = None):
        """
        设置缓存数据
        
        Args:
            key: 缓存键
            value: 缓存值
            expires_in: 过期时间，可选
        """
        try:
            serialized = json.dumps(value)
            if expires_in:
                self.client.setex(key, expires_in, serialized)
            else:
                self.client.set(key, serialized)
        except Exception:
            pass

    async def delete(self, key: str):
        """
        删除缓存数据
        
        Args:
            key: 缓存键
        """
        try:
            self.client.delete(key)
        except Exception:
            pass

    async def exists(self, key: str) -> bool:
        """
        检查缓存键是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 存在返回True，否则返回False
        """
        try:
            return self.client.exists(key) > 0
        except Exception:
            return False

    async def get_or_set(self, key: str, default_func: Callable[[], Any], expires_in: Optional[timedelta] = None):
        """
        获取或设置缓存
        
        如果缓存存在则返回缓存值，否则执行默认函数获取值并设置缓存。
        
        Args:
            key: 缓存键
            default_func: 默认值生成函数
            expires_in: 过期时间，可选
            
        Returns:
            Any: 缓存值或默认函数返回的值
        """
        value = await self.get(key)
        if value is not None:
            return value
        value = default_func()
        await self.set(key, value, expires_in)
        return value

    async def publish(self, channel: str, message: Any):
        """
        发布消息到指定频道
        
        Args:
            channel: 频道名称
            message: 消息内容
        """
        try:
            serialized = json.dumps(message)
            self.client.publish(channel, serialized)
        except Exception:
            pass

    async def subscribe(self, channel: str):
        """
        订阅指定频道
        
        Args:
            channel: 频道名称
            
        Returns:
            pubsub: Redis发布订阅对象
        """
        pubsub = self.client.pubsub()
        pubsub.subscribe(channel)
        return pubsub


class CacheKeys:
    """
    缓存键名管理器
    
    提供统一的缓存键名生成方法，避免硬编码键名导致的错误。
    """
    
    COMPANY_PREFIX = "company:"
    JOB_PREFIX = "job:"
    CANDIDATE_PREFIX = "candidate:"
    MATCH_PREFIX = "match:"
    PROCESS_PREFIX = "process:"

    @classmethod
    def company_key(cls, company_id: str) -> str:
        """
        生成企业缓存键
        
        Args:
            company_id: 企业ID
            
        Returns:
            str: 企业缓存键
        """
        return f"{cls.COMPANY_PREFIX}{company_id}"

    @classmethod
    def job_key(cls, job_id: str) -> str:
        """
        生成岗位缓存键
        
        Args:
            job_id: 岗位ID
            
        Returns:
            str: 岗位缓存键
        """
        return f"{cls.JOB_PREFIX}{job_id}"

    @classmethod
    def candidate_key(cls, candidate_id: str) -> str:
        """
        生成候选人缓存键
        
        Args:
            candidate_id: 候选人ID
            
        Returns:
            str: 候选人缓存键
        """
        return f"{cls.CANDIDATE_PREFIX}{candidate_id}"

    @classmethod
    def match_key(cls, match_id: str) -> str:
        """
        生成匹配记录缓存键
        
        Args:
            match_id: 匹配记录ID
            
        Returns:
            str: 匹配记录缓存键
        """
        return f"{cls.MATCH_PREFIX}{match_id}"

    @classmethod
    def process_key(cls, match_id: str) -> str:
        """
        生成流程缓存键
        
        Args:
            match_id: 匹配记录ID
            
        Returns:
            str: 流程缓存键
        """
        return f"{cls.PROCESS_PREFIX}{match_id}"

    @classmethod
    def company_jobs_key(cls, company_id: str) -> str:
        """
        生成企业岗位列表缓存键
        
        Args:
            company_id: 企业ID
            
        Returns:
            str: 企业岗位列表缓存键
        """
        return f"{cls.COMPANY_PREFIX}{company_id}:jobs"

    @classmethod
    def job_matches_key(cls, job_id: str) -> str:
        """
        生成岗位匹配列表缓存键
        
        Args:
            job_id: 岗位ID
            
        Returns:
            str: 岗位匹配列表缓存键
        """
        return f"{cls.JOB_PREFIX}{job_id}:matches"

    @classmethod
    def candidate_matches_key(cls, candidate_id: str) -> str:
        """
        生成候选人匹配列表缓存键
        
        Args:
            candidate_id: 候选人ID
            
        Returns:
            str: 候选人匹配列表缓存键
        """
        return f"{cls.CANDIDATE_PREFIX}{candidate_id}:matches"


cache = RedisCache()
