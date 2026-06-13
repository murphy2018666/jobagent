from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool, NullPool
from typing import Optional, AsyncIterator, Callable, Any
from loguru import logger
from ..config.settings import settings


class DatabaseCluster:
    """
    数据库集群管理（读写分离）
    
    实现数据库读写分离，支持主库写操作和从库读操作，提供负载均衡和故障转移能力。
    """
    
    def __init__(self):
        """
        初始化数据库集群
        
        创建写引擎和读引擎列表，配置连接池参数。
        """
        self.read_engines = []
        self.write_engine = None
        self.read_sessions = []
        self.write_session = None
        self.read_index = 0
        self._init_engines()
    
    def _init_engines(self):
        """
        初始化数据库引擎
        
        创建主库写引擎和从库读引擎，配置连接池参数包括池大小、最大溢出、超时时间等。
        """
        # 主库（写操作）
        self.write_engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            poolclass=QueuePool,
            pool_size=20,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
        )
        
        # 从库列表（读操作）
        read_replicas = settings.READ_REPLICAS or []
        for i, replica_url in enumerate(read_replicas):
            engine = create_async_engine(
                replica_url,
                echo=False,
                poolclass=QueuePool,
                pool_size=15,
                max_overflow=5,
                pool_timeout=30,
                pool_recycle=1800,
            )
            self.read_engines.append(engine)
            session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            self.read_sessions.append(session)
        
        # 如果没有从库，使用主库进行读操作
        if not self.read_engines:
            self.read_engines.append(self.write_engine)
            self.read_sessions.append(sessionmaker(self.write_engine, class_=AsyncSession, expire_on_commit=False))
        
        logger.info(f"Database cluster initialized: 1 write engine, {len(self.read_engines)} read engines")
    
    def get_write_session(self) -> sessionmaker:
        """
        获取写会话工厂
        
        Returns:
            sessionmaker: 写操作会话工厂
        """
        return sessionmaker(self.write_engine, class_=AsyncSession, expire_on_commit=False)
    
    def get_read_session(self) -> sessionmaker:
        """
        获取读会话工厂（轮询）
        
        使用轮询策略从多个从库中选择一个进行读操作，实现负载均衡。
        
        Returns:
            sessionmaker: 读操作会话工厂
        """
        session = self.read_sessions[self.read_index % len(self.read_sessions)]
        self.read_index += 1
        return session
    
    async def get_write_session_async(self) -> AsyncIterator[AsyncSession]:
        """
        异步获取写会话
        
        Yields:
            AsyncSession: 写操作会话
        """
        async with self.get_write_session()() as session:
            yield session
    
    async def get_read_session_async(self) -> AsyncIterator[AsyncSession]:
        """
        异步获取读会话
        
        Yields:
            AsyncSession: 读操作会话
        """
        async with self.get_read_session()() as session:
            yield session
    
    def health_check(self) -> dict:
        """
        检查数据库健康状态
        
        检查主库和所有从库的连接状态，返回健康检查结果。
        
        Returns:
            dict: 健康检查结果，包含写引擎和所有读引擎的状态
        """
        results = {
            "write": {"healthy": True, "error": None},
            "read": []
        }
        
        import asyncio
        
        async def check_engine(engine, name):
            """检查单个引擎的健康状态"""
            try:
                async with engine.connect() as conn:
                    await conn.execute("SELECT 1")
                return {"name": name, "healthy": True, "error": None}
            except Exception as e:
                logger.error(f"Database health check failed for {name}: {str(e)}")
                return {"name": name, "healthy": False, "error": str(e)}
        
        # 检查写引擎
        write_result = asyncio.run(check_engine(self.write_engine, "write"))
        results["write"] = write_result
        
        # 检查读引擎
        for i, engine in enumerate(self.read_engines):
            read_result = asyncio.run(check_engine(engine, f"read_{i}"))
            results["read"].append(read_result)
        
        return results
    
    async def close(self):
        """
        关闭所有引擎
        
        释放数据库连接池资源，优雅关闭数据库集群。
        """
        for engine in self.read_engines:
            await engine.dispose()
        await self.write_engine.dispose()
        logger.info("Database cluster closed")


class ShardingRouter:
    """
    数据分片路由器
    
    根据实体ID计算分片位置，支持水平分片场景。
    """
    
    def __init__(self, shard_count: int = 4):
        """
        初始化分片路由器
        
        Args:
            shard_count: 分片数量，默认为4
        """
        self.shard_count = shard_count
    
    def get_shard_id(self, entity_id: str) -> int:
        """
        根据实体ID计算分片ID
        
        使用MD5哈希算法对实体ID进行哈希，然后取模得到分片ID。
        
        Args:
            entity_id: 实体ID
            
        Returns:
            int: 分片ID（0到shard_count-1）
        """
        import hashlib
        hash_value = hashlib.md5(entity_id.encode()).hexdigest()
        return int(hash_value, 16) % self.shard_count
    
    def route_to_shard(self, entity_id: str) -> str:
        """
        路由到对应的分片
        
        Args:
            entity_id: 实体ID
            
        Returns:
            str: 分片名称，格式为"shard_{shard_id}"
        """
        shard_id = self.get_shard_id(entity_id)
        return f"shard_{shard_id}"


class QueryHint:
    """
    查询提示器
    
    定义查询操作的类型提示，用于指导事务管理器选择合适的数据库连接。
    """
    
    READ_ONLY = "read_only"      # 只读操作，只能使用从库
    WRITE_ONLY = "write_only"    # 只写操作，只能使用主库
    PREFER_READ = "prefer_read"  # 优先读，可降级到主库
    PREFER_WRITE = "prefer_write"# 优先写


class TransactionManager:
    """
    事务管理器
    
    提供统一的事务管理接口，支持读操作、写操作和多步骤事务。
    """
    
    def __init__(self, db_cluster: DatabaseCluster):
        """
        初始化事务管理器
        
        Args:
            db_cluster: 数据库集群实例
        """
        self.db_cluster = db_cluster
    
    async def execute_read(self, query_func: Callable[[AsyncSession], Any], hint: str = QueryHint.PREFER_READ):
        """
        执行只读操作
        
        根据查询提示选择合适的数据库连接，支持从库故障时自动降级到主库。
        
        Args:
            query_func: 查询函数，接收会话参数
            hint: 查询提示，默认为PREFER_READ
            
        Returns:
            Any: 查询结果
        """
        if hint == QueryHint.WRITE_ONLY:
            async for session in self.db_cluster.get_write_session_async():
                return await query_func(session)
        
        async for session in self.db_cluster.get_read_session_async():
            try:
                return await query_func(session)
            except Exception as e:
                logger.warning(f"Read from replica failed, falling back to write: {str(e)}")
                async for write_session in self.db_cluster.get_write_session_async():
                    return await query_func(write_session)
    
    async def execute_write(self, query_func: Callable[[AsyncSession], Any]):
        """
        执行写操作
        
        使用主库连接执行写操作，自动处理事务提交和回滚。
        
        Args:
            query_func: 写操作函数，接收会话参数
            
        Returns:
            Any: 操作结果
            
        Raises:
            Exception: 写操作失败时抛出异常
        """
        async for session in self.db_cluster.get_write_session_async():
            try:
                result = await query_func(session)
                await session.commit()
                return result
            except Exception as e:
                await session.rollback()
                raise
    
    async def execute_transaction(self, operations: list):
        """
        执行多步骤事务
        
        在一个事务中执行多个操作，保证原子性。
        
        Args:
            operations: 操作列表，每个操作是一个接收会话参数的函数
            
        Returns:
            list: 每个操作的返回结果
            
        Raises:
            Exception: 事务失败时抛出异常
        """
        async for session in self.db_cluster.get_write_session_async():
            try:
                results = []
                for op in operations:
                    result = await op(session)
                    results.append(result)
                await session.commit()
                return results
            except Exception as e:
                await session.rollback()
                logger.error(f"Transaction failed: {str(e)}")
                raise


# 全局数据库集群实例
db_cluster = DatabaseCluster()
sharding_router = ShardingRouter()
transaction_manager = TransactionManager(db_cluster)
