import redis
import time
import uuid
from typing import Optional, Any, Dict
from contextlib import contextmanager
from loguru import logger
from ..config.settings import settings


class DistributedLock:
    """
    基于Redis的分布式锁实现
    
    使用SET NX命令实现原子性锁获取，支持自动过期和锁释放保护。
    """
    
    def __init__(self, client: redis.Redis = None):
        """
        初始化分布式锁
        
        Args:
            client: Redis客户端实例，默认为None时使用配置中的Redis连接
        """
        self.client = client or redis.from_url(settings.REDIS_URL)
        self.lock_prefix = "lock:"
    
    @contextmanager
    def acquire(self, lock_key: str, timeout: int = 10, wait_timeout: int = 30):
        """
        获取分布式锁
        
        使用with语句自动管理锁的获取和释放。
        
        Args:
            lock_key: 锁的键名
            timeout: 锁的自动过期时间（秒），默认为10秒
            wait_timeout: 等待获取锁的最大时间（秒），默认为30秒
            
        Yields:
            bool: 获取锁成功返回True，超时返回False
        """
        full_key = f"{self.lock_prefix}{lock_key}"
        identifier = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            while time.time() - start_time < wait_timeout:
                # 使用SET NX获取锁
                result = self.client.set(full_key, identifier, ex=timeout, nx=True)
                if result:
                    logger.debug(f"Acquired lock: {lock_key}")
                    yield True
                    return
                
                time.sleep(0.1)
            
            logger.warning(f"Timeout waiting for lock: {lock_key}")
            yield False
        finally:
            # 释放锁（只能释放自己的锁）
            current_value = self.client.get(full_key)
            if current_value and current_value.decode() == identifier:
                self.client.delete(full_key)
                logger.debug(f"Released lock: {lock_key}")
    
    def is_locked(self, lock_key: str) -> bool:
        """
        检查锁是否被持有
        
        Args:
            lock_key: 锁的键名
            
        Returns:
            bool: 锁被持有返回True，否则返回False
        """
        full_key = f"{self.lock_prefix}{lock_key}"
        return self.client.exists(full_key) > 0


class DistributedIDGenerator:
    """
    分布式ID生成器
    
    基于Snowflake算法思想，结合Redis原子递增生成全局唯一ID。
    结构：timestamp(41位) + data_center(5位) + worker(5位) + sequence(12位)
    """
    
    def __init__(self, client: redis.Redis = None):
        """
        初始化ID生成器
        
        Args:
            client: Redis客户端实例，默认为None时使用配置中的Redis连接
        """
        self.client = client or redis.from_url(settings.REDIS_URL)
        self.counter_prefix = "id:"
    
    def generate(self, namespace: str) -> str:
        """
        生成分布式ID
        
        Args:
            namespace: ID命名空间，用于区分不同业务类型
            
        Returns:
            str: 生成的全局唯一ID
        """
        # 使用Redis原子递增获取序列号
        counter_key = f"{self.counter_prefix}{namespace}"
        sequence = self.client.incr(counter_key)
        
        # 生成Snowflake风格ID
        timestamp = int(time.time() * 1000)
        worker_id = self._get_worker_id()
        data_center_id = self._get_data_center_id()
        
        # 组合ID: timestamp(41位) + data_center(5位) + worker(5位) + sequence(12位)
        return f"{timestamp}{data_center_id:02d}{worker_id:02d}{sequence:04d}"
    
    def _get_worker_id(self) -> int:
        """
        获取工作节点ID
        
        通过主机名哈希生成，确保同一节点的worker_id一致。
        
        Returns:
            int: 工作节点ID（0-31）
        """
        import socket
        try:
            hostname = socket.gethostname()
            return abs(hash(hostname)) % 32
        except:
            return 0
    
    def _get_data_center_id(self) -> int:
        """
        获取数据中心ID
        
        Returns:
            int: 数据中心ID，默认返回1（可配置为不同数据中心）
        """
        return 1  # 可配置为不同数据中心
    
    def reset_counter(self, namespace: str):
        """
        重置指定命名空间的计数器
        
        Args:
            namespace: ID命名空间
        """
        counter_key = f"{self.counter_prefix}{namespace}"
        self.client.delete(counter_key)


class DistributedCache:
    """
    分布式缓存服务
    
    基于Redis实现的缓存服务，支持JSON序列化和TTL过期。
    """
    
    def __init__(self, client: redis.Redis = None):
        """
        初始化缓存服务
        
        Args:
            client: Redis客户端实例，默认为None时使用配置中的Redis连接
        """
        self.client = client or redis.from_url(settings.REDIS_URL)
    
    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键名
            
        Returns:
            Optional[Any]: 缓存值，如果不存在返回None
        """
        import json
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Get cache failed: {str(e)}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        设置缓存值
        
        Args:
            key: 缓存键名
            value: 缓存值（会被JSON序列化）
            ttl: 过期时间（秒），默认为None表示永不过期
        """
        import json
        try:
            serialized = json.dumps(value)
            if ttl:
                self.client.setex(key, ttl, serialized)
            else:
                self.client.set(key, serialized)
        except Exception as e:
            logger.error(f"Set cache failed: {str(e)}")
    
    async def delete(self, key: str):
        """
        删除缓存
        
        Args:
            key: 缓存键名
        """
        try:
            self.client.delete(key)
        except Exception as e:
            logger.error(f"Delete cache failed: {str(e)}")
    
    async def exists(self, key: str) -> bool:
        """
        检查缓存是否存在
        
        Args:
            key: 缓存键名
            
        Returns:
            bool: 缓存存在返回True，否则返回False
        """
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Exists check failed: {str(e)}")
            return False
    
    async def invalidate_pattern(self, pattern: str):
        """
        删除匹配模式的缓存
        
        Args:
            pattern: 键名匹配模式，如"job:*"
        """
        try:
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache keys matching: {pattern}")
        except Exception as e:
            logger.error(f"Invalidate pattern failed: {str(e)}")
    
    async def get_or_set(self, key: str, default_func: callable, ttl: Optional[int] = None) -> Any:
        """
        获取缓存，不存在则设置
        
        Args:
            key: 缓存键名
            default_func: 生成默认值的函数
            ttl: 过期时间（秒）
            
        Returns:
            Any: 缓存值
        """
        value = await self.get(key)
        if value is not None:
            return value
        
        value = default_func()
        await self.set(key, value, ttl)
        return value


class RateLimiter:
    """
    基于Redis的限流器
    
    使用Redis计数器实现简单的滑动窗口限流。
    """
    
    def __init__(self, client: redis.Redis = None):
        """
        初始化限流器
        
        Args:
            client: Redis客户端实例，默认为None时使用配置中的Redis连接
        """
        self.client = client or redis.from_url(settings.REDIS_URL)
        self.prefix = "rate_limit:"
    
    def is_allowed(self, key: str, limit: int, window_seconds: int) -> bool:
        """
        检查是否允许请求
        
        Args:
            key: 限流键名（通常为用户ID或IP）
            limit: 时间窗口内的最大请求次数
            window_seconds: 时间窗口大小（秒）
            
        Returns:
            bool: 允许请求返回True，否则返回False
        """
        full_key = f"{self.prefix}{key}"
        current = self.client.incr(full_key)
        
        if current == 1:
            # 首次请求，设置过期时间
            self.client.expire(full_key, window_seconds)
        
        return current <= limit
    
    def get_remaining(self, key: str, limit: int) -> int:
        """
        获取剩余请求次数
        
        Args:
            key: 限流键名
            limit: 时间窗口内的最大请求次数
            
        Returns:
            int: 剩余请求次数
        """
        full_key = f"{self.prefix}{key}"
        current = int(self.client.get(full_key) or 0)
        return max(0, limit - current)


# 全局实例
distributed_lock = DistributedLock()
id_generator = DistributedIDGenerator()
distributed_cache = DistributedCache()
rate_limiter = RateLimiter()
