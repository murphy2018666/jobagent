import redis
import time
from typing import Optional, Callable, Any, Dict
from functools import wraps
from loguru import logger
from ..config.settings import settings


class CircuitBreaker:
    """
    熔断器模式实现
    
    熔断器用于保护系统免受级联故障影响，实现三种状态：
    - Closed（关闭）：正常状态，允许所有请求通过
    - Open（打开）：故障状态，拒绝所有请求
    - Half-Open（半开）：恢复状态，允许有限数量的请求试探服务是否恢复
    
    使用Redis存储状态信息，支持分布式环境下的状态共享。
    """
    
    def __init__(
        self,
        client: redis.Redis = None,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        half_open_max_requests: int = 3,
    ):
        """
        初始化熔断器
        
        Args:
            client: Redis客户端实例，默认为None时使用配置中的Redis连接
            failure_threshold: 失败阈值，超过此值熔断器打开，默认为5
            recovery_timeout: 恢复超时时间（秒），熔断器打开后经过此时间进入半开状态，默认为30秒
            half_open_max_requests: 半开状态允许的最大请求数，默认为3
        """
        self.client = client or redis.from_url(settings.REDIS_URL)
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_requests = half_open_max_requests
        self.prefix = "circuit_breaker:"
    
    def _get_state(self, service: str) -> bytes:
        """
        获取熔断器状态
        
        Args:
            service: 服务名称
            
        Returns:
            bytes: 状态值（closed/open/half_open）
        """
        state_key = f"{self.prefix}{service}:state"
        return self.client.get(state_key) or b"closed"
    
    def _set_state(self, service: str, state: str):
        """
        设置熔断器状态
        
        Args:
            service: 服务名称
            state: 状态值（closed/open/half_open）
        """
        state_key = f"{self.prefix}{service}:state"
        self.client.set(state_key, state)
    
    def _get_failure_count(self, service: str) -> int:
        """
        获取失败计数
        
        Args:
            service: 服务名称
            
        Returns:
            int: 失败次数
        """
        count_key = f"{self.prefix}{service}:failures"
        return int(self.client.get(count_key) or 0)
    
    def _increment_failure(self, service: str):
        """
        增加失败计数
        
        Args:
            service: 服务名称
        """
        count_key = f"{self.prefix}{service}:failures"
        self.client.incr(count_key)
    
    def _reset_failure_count(self, service: str):
        """
        重置失败计数
        
        Args:
            service: 服务名称
        """
        count_key = f"{self.prefix}{service}:failures"
        self.client.delete(count_key)
    
    def _get_last_failure_time(self, service: str) -> float:
        """
        获取最后失败时间
        
        Args:
            service: 服务名称
            
        Returns:
            float: 最后失败时间戳
        """
        time_key = f"{self.prefix}{service}:last_failure"
        return float(self.client.get(time_key) or 0)
    
    def _set_last_failure_time(self, service: str):
        """
        设置最后失败时间
        
        Args:
            service: 服务名称
        """
        time_key = f"{self.prefix}{service}:last_failure"
        self.client.set(time_key, time.time())
    
    def _get_half_open_count(self, service: str) -> int:
        """
        获取半开状态请求计数
        
        Args:
            service: 服务名称
            
        Returns:
            int: 半开状态下已处理的请求数
        """
        count_key = f"{self.prefix}{service}:half_open_count"
        return int(self.client.get(count_key) or 0)
    
    def _increment_half_open_count(self, service: str):
        """
        增加半开状态请求计数
        
        Args:
            service: 服务名称
        """
        count_key = f"{self.prefix}{service}:half_open_count"
        self.client.incr(count_key)
    
    def _reset_half_open_count(self, service: str):
        """
        重置半开状态请求计数
        
        Args:
            service: 服务名称
        """
        count_key = f"{self.prefix}{service}:half_open_count"
        self.client.delete(count_key)
    
    def _should_open(self, service: str) -> bool:
        """
        判断是否应该打开熔断器
        
        Args:
            service: 服务名称
            
        Returns:
            bool: 应该打开返回True
        """
        failures = self._get_failure_count(service)
        return failures >= self.failure_threshold
    
    def _should_attempt_reset(self, service: str) -> bool:
        """
        判断是否应该尝试重置（进入半开状态）
        
        Args:
            service: 服务名称
            
        Returns:
            bool: 应该尝试重置返回True
        """
        last_failure = self._get_last_failure_time(service)
        return (time.time() - last_failure) >= self.recovery_timeout
    
    def _is_half_open_limit_reached(self, service: str) -> bool:
        """
        判断半开状态请求是否达到上限
        
        Args:
            service: 服务名称
            
        Returns:
            bool: 达到上限返回True
        """
        count = self._get_half_open_count(service)
        return count >= self.half_open_max_requests
    
    def call(self, service: str, func: Callable, *args, **kwargs) -> Any:
        """
        执行受保护的调用
        
        Args:
            service: 服务名称
            func: 要执行的函数
            *args: 函数位置参数
            **kwargs: 函数关键字参数
            
        Returns:
            Any: 函数执行结果
            
        Raises:
            CircuitBreakerError: 熔断器打开时抛出
            Exception: 原始函数的异常
        """
        state = self._get_state(service).decode()
        
        # 熔断器打开状态
        if state == "open":
            if self._should_attempt_reset(service):
                # 进入半开状态
                self._set_state(service, "half_open")
                self._reset_half_open_count(service)
                logger.info(f"Circuit breaker {service} transitioning to half-open state")
            else:
                logger.warning(f"Circuit breaker {service} is open, rejecting request")
                raise CircuitBreakerError(f"Service {service} is unavailable")
        
        # 半开状态限制请求数量
        if state == "half_open" and self._is_half_open_limit_reached(service):
            logger.warning(f"Circuit breaker {service} half-open limit reached")
            raise CircuitBreakerError(f"Service {service} is in recovery")
        
        try:
            # 执行调用
            result = func(*args, **kwargs)
            
            # 成功，重置熔断器
            if state != "closed":
                self._set_state(service, "closed")
                self._reset_failure_count(service)
                self._reset_half_open_count(service)
                logger.info(f"Circuit breaker {service} reset to closed state")
            
            return result
        
        except Exception as e:
            # 失败，增加失败计数
            self._increment_failure(service)
            self._set_last_failure_time(service)
            
            if state == "half_open":
                self._increment_half_open_count(service)
            
            # 判断是否需要打开熔断器
            if self._should_open(service):
                self._set_state(service, "open")
                logger.warning(f"Circuit breaker {service} opened due to failures")
            
            raise
    
    def decorate(self, service: str):
        """
        装饰器工厂
        
        Args:
            service: 服务名称
            
        Returns:
            Callable: 装饰器函数
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                return self.call(service, func, *args, **kwargs)
            return wrapper
        return decorator


class CircuitBreakerError(Exception):
    """
    熔断器异常
    
    当熔断器打开时尝试调用服务抛出此异常。
    """
    pass


class LoadBalancer:
    """
    简单的负载均衡器
    
    支持多种负载均衡策略：轮询、随机、最小负载（预留）。
    """
    
    def __init__(self, servers: list = None):
        """
        初始化负载均衡器
        
        Args:
            servers: 服务器列表，默认为空列表
        """
        self.servers = servers or []
        self.index = 0
    
    def add_server(self, server: str):
        """
        添加服务器
        
        Args:
            server: 服务器地址
        """
        if server not in self.servers:
            self.servers.append(server)
    
    def remove_server(self, server: str):
        """
        移除服务器
        
        Args:
            server: 服务器地址
        """
        if server in self.servers:
            self.servers.remove(server)
    
    def get_next_server(self) -> Optional[str]:
        """
        获取下一个服务器（轮询策略）
        
        Returns:
            Optional[str]: 服务器地址，如果没有服务器返回None
        """
        if not self.servers:
            return None
        
        server = self.servers[self.index % len(self.servers)]
        self.index += 1
        return server
    
    def get_random_server(self) -> Optional[str]:
        """
        随机获取服务器
        
        Returns:
            Optional[str]: 服务器地址，如果没有服务器返回None
        """
        if not self.servers:
            return None
        
        import random
        return random.choice(self.servers)
    
    def get_least_loaded_server(self) -> Optional[str]:
        """
        获取负载最小的服务器（需要健康检查支持）
        
        当前实现返回第一个服务器，预留接口用于后续扩展。
        
        Returns:
            Optional[str]: 服务器地址，如果没有服务器返回None
        """
        if not self.servers:
            return None
        return self.servers[0]


class HealthChecker:
    """
    健康检查服务
    
    用于监控服务健康状态，支持多次失败后标记服务为不健康。
    """
    
    def __init__(self, client: redis.Redis = None):
        """
        初始化健康检查服务
        
        Args:
            client: Redis客户端实例，默认为None时使用配置中的Redis连接
        """
        self.client = client or redis.from_url(settings.REDIS_URL)
        self.health_prefix = "health:"
        self.unhealthy_threshold = 3
    
    def report_health(self, service: str, healthy: bool):
        """
        报告服务健康状态
        
        Args:
            service: 服务名称
            healthy: 健康状态，True表示健康，False表示不健康
        """
        status_key = f"{self.health_prefix}{service}:status"
        count_key = f"{self.health_prefix}{service}:unhealthy_count"
        
        if healthy:
            self.client.set(status_key, "healthy")
            self.client.delete(count_key)
        else:
            count = self.client.incr(count_key)
            if count >= self.unhealthy_threshold:
                self.client.set(status_key, "unhealthy")
                logger.warning(f"Service {service} marked as unhealthy")
    
    def is_healthy(self, service: str) -> bool:
        """
        检查服务是否健康
        
        Args:
            service: 服务名称
            
        Returns:
            bool: 健康返回True，否则返回False
        """
        status_key = f"{self.health_prefix}{service}:status"
        status = self.client.get(status_key)
        return status == b"healthy" or status is None
    
    def get_all_health_status(self) -> Dict[str, str]:
        """
        获取所有服务健康状态
        
        Returns:
            Dict[str, str]: 服务名称到健康状态的映射
        """
        status = {}
        keys = self.client.keys(f"{self.health_prefix}*:status")
        for key in keys:
            service = key.decode().replace(f"{self.health_prefix}", "").replace(":status", "")
            status[service] = self.client.get(key).decode()
        return status


# 全局实例
circuit_breaker = CircuitBreaker()
load_balancer = LoadBalancer()
health_checker = HealthChecker()
