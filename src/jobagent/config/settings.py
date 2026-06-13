from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "Job Agent"
    APP_VERSION: str = "1.0.0"
    
    # 数据库配置
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/jobagent"
    READ_REPLICAS: Optional[List[str]] = None
    
    # 数据库连接池配置
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    
    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT 配置
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # MCP 配置
    MCP_PROTOCOL_VERSION: str = "v1"
    MCP_TIMEOUT_SECONDS: int = 30
    
    # 匹配配置
    MATCH_TOP_N: int = 10
    MATCH_SCORE_THRESHOLD: float = 0.6
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    
    # 限流配置
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    
    # 熔断器配置
    CIRCUIT_BREAKER_ENABLED: bool = True
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 30
    CIRCUIT_BREAKER_HALF_OPEN_MAX_REQUESTS: int = 3
    
    # 异步任务配置
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None
    TASK_TIMEOUT_SECONDS: int = 300
    
    # 分布式锁配置
    LOCK_TIMEOUT_SECONDS: int = 10
    LOCK_WAIT_TIMEOUT_SECONDS: int = 30
    
    # 缓存配置
    CACHE_DEFAULT_TTL: int = 300
    CACHE_ENABLED: bool = True
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
