from fastapi import FastAPI, Depends, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from typing import Optional
from .config.settings import settings
from .config.logging import configure_logging
from .interfaces.api import router as api_router
from .interfaces.evaluation_api import router as evaluation_router
from .interfaces.mcp_gateway import mcp_router
from .infrastructure.database import init_db, get_session
from .infrastructure.database_cluster import db_cluster, transaction_manager
from .infrastructure.distributed import rate_limiter
from .infrastructure.circuit_breaker import circuit_breaker, health_checker
from .infrastructure.security import SecurityServiceImpl, JWTService, AuthMiddleware
from .infrastructure.mcp_protocol import McpProtocolServiceImpl
from .infrastructure.matching_engine import MatchingServiceImpl
from .application.services import (
    CompanyApplicationService,
    JobApplicationService,
    CandidateApplicationService,
    MatchApplicationService,
    ProcessApplicationService,
    SearchApplicationService,
)
from .domain.repositories import (
    CompanyRepository,
    JobRepository,
    CandidateRepository,
    MatchRepository,
    ProcessRepository,
)
from .infrastructure.database import (
    DatabaseCompanyRepository,
    DatabaseJobRepository,
    DatabaseCandidateRepository,
    DatabaseMatchRepository,
    DatabaseProcessRepository,
)


# 配置日志
configure_logging(settings.LOG_LEVEL)


# 依赖注入：仓储层
async def get_company_repo(session=Depends(get_session)) -> CompanyRepository:
    """
    获取企业仓储实例
    
    Args:
        session: SQLAlchemy异步会话（自动注入）
        
    Returns:
        CompanyRepository: 企业仓储实例
    """
    return DatabaseCompanyRepository(session)


async def get_job_repo(session=Depends(get_session)) -> JobRepository:
    """
    获取岗位仓储实例
    
    Args:
        session: SQLAlchemy异步会话（自动注入）
        
    Returns:
        JobRepository: 岗位仓储实例
    """
    return DatabaseJobRepository(session)


async def get_candidate_repo(session=Depends(get_session)) -> CandidateRepository:
    """
    获取候选人仓储实例
    
    Args:
        session: SQLAlchemy异步会话（自动注入）
        
    Returns:
        CandidateRepository: 候选人仓储实例
    """
    return DatabaseCandidateRepository(session)


async def get_match_repo(session=Depends(get_session)) -> MatchRepository:
    """
    获取匹配仓储实例
    
    Args:
        session: SQLAlchemy异步会话（自动注入）
        
    Returns:
        MatchRepository: 匹配仓储实例
    """
    return DatabaseMatchRepository(session)


async def get_process_repo(session=Depends(get_session)) -> ProcessRepository:
    """
    获取流程仓储实例
    
    Args:
        session: SQLAlchemy异步会话（自动注入）
        
    Returns:
        ProcessRepository: 流程仓储实例
    """
    return DatabaseProcessRepository(session)


# 依赖注入：基础设施服务
async def get_mcp_service(
    company_repo=Depends(get_company_repo),
    candidate_repo=Depends(get_candidate_repo),
):
    """
    获取MCP协议服务实例
    
    Args:
        company_repo: 企业仓储实例
        candidate_repo: 候选人仓储实例
        
    Returns:
        McpProtocolServiceImpl: MCP协议服务实例
    """
    return McpProtocolServiceImpl(company_repo, candidate_repo)


async def get_matching_service(
    job_repo=Depends(get_job_repo),
    candidate_repo=Depends(get_candidate_repo),
    match_repo=Depends(get_match_repo),
):
    """
    获取匹配引擎服务实例
    
    Args:
        job_repo: 岗位仓储实例
        candidate_repo: 候选人仓储实例
        match_repo: 匹配仓储实例
        
    Returns:
        MatchingServiceImpl: 匹配引擎服务实例
    """
    return MatchingServiceImpl(job_repo, candidate_repo, match_repo)


async def get_security_service():
    """
    获取安全服务实例
    
    Returns:
        SecurityServiceImpl: 安全服务实例
    """
    return SecurityServiceImpl(settings.SECRET_KEY)


async def get_jwt_service():
    """
    获取JWT服务实例
    
    Returns:
        JWTService: JWT服务实例
    """
    return JWTService(settings.SECRET_KEY, settings.ALGORITHM)


async def get_auth_middleware(
    company_repo=Depends(get_company_repo),
    candidate_repo=Depends(get_candidate_repo),
    jwt_service=Depends(get_jwt_service),
):
    """
    获取认证中间件实例
    
    Args:
        company_repo: 企业仓储实例
        candidate_repo: 候选人仓储实例
        jwt_service: JWT服务实例
        
    Returns:
        AuthMiddleware: 认证中间件实例
    """
    return AuthMiddleware(company_repo, candidate_repo, jwt_service)


# 依赖注入：应用服务层
async def get_company_service(
    company_repo=Depends(get_company_repo),
) -> CompanyApplicationService:
    """
    获取企业应用服务实例
    
    Args:
        company_repo: 企业仓储实例
        
    Returns:
        CompanyApplicationService: 企业应用服务实例
    """
    return CompanyApplicationService(company_repo)


async def get_job_service(
    job_repo=Depends(get_job_repo),
    company_repo=Depends(get_company_repo),
    mcp_service=Depends(get_mcp_service),
) -> JobApplicationService:
    """
    获取岗位应用服务实例
    
    Args:
        job_repo: 岗位仓储实例
        company_repo: 企业仓储实例
        mcp_service: MCP协议服务实例
        
    Returns:
        JobApplicationService: 岗位应用服务实例
    """
    return JobApplicationService(job_repo, company_repo, mcp_service)


async def get_candidate_service(
    candidate_repo=Depends(get_candidate_repo),
    security_service=Depends(get_security_service),
    mcp_service=Depends(get_mcp_service),
) -> CandidateApplicationService:
    """
    获取候选人应用服务实例
    
    Args:
        candidate_repo: 候选人仓储实例
        security_service: 安全服务实例
        mcp_service: MCP协议服务实例
        
    Returns:
        CandidateApplicationService: 候选人应用服务实例
    """
    return CandidateApplicationService(candidate_repo, security_service, mcp_service)


async def get_match_service(
    match_repo=Depends(get_match_repo),
    job_repo=Depends(get_job_repo),
    candidate_repo=Depends(get_candidate_repo),
    process_repo=Depends(get_process_repo),
    matching_service=Depends(get_matching_service),
) -> MatchApplicationService:
    """
    获取匹配应用服务实例
    
    Args:
        match_repo: 匹配仓储实例
        job_repo: 岗位仓储实例
        candidate_repo: 候选人仓储实例
        process_repo: 流程仓储实例
        matching_service: 匹配引擎服务实例
        
    Returns:
        MatchApplicationService: 匹配应用服务实例
    """
    return MatchApplicationService(match_repo, job_repo, candidate_repo, process_repo, matching_service)


async def get_process_service(
    process_repo=Depends(get_process_repo),
    match_repo=Depends(get_match_repo),
    mcp_service=Depends(get_mcp_service),
) -> ProcessApplicationService:
    """
    获取流程应用服务实例
    
    Args:
        process_repo: 流程仓储实例
        match_repo: 匹配仓储实例
        mcp_service: MCP协议服务实例
        
    Returns:
        ProcessApplicationService: 流程应用服务实例
    """
    return ProcessApplicationService(process_repo, match_repo, mcp_service)


async def get_search_service(
    candidate_repo=Depends(get_candidate_repo),
    security_service=Depends(get_security_service),
) -> SearchApplicationService:
    """
    获取搜索应用服务实例
    
    Args:
        candidate_repo: 候选人仓储实例
        security_service: 安全服务实例
        
    Returns:
        SearchApplicationService: 搜索应用服务实例
    """
    return SearchApplicationService(candidate_repo, security_service)


# 创建FastAPI应用实例
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Job Agent 智能招聘匹配平台 API",
)


# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """
    限流中间件
    
    基于Redis实现的请求限流，保护系统免受流量冲击。
    
    Args:
        request: FastAPI请求对象
        call_next: 下一个中间件或路由处理函数
        
    Returns:
        JSONResponse: 响应对象，超过限流时返回429状态码
    """
    if not settings.RATE_LIMIT_ENABLED:
        return await call_next(request)
    
    client_ip = request.client.host
    if not rate_limiter.is_allowed(client_ip, settings.RATE_LIMIT_REQUESTS, settings.RATE_LIMIT_WINDOW_SECONDS):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Rate limit exceeded"}
        )
    
    response = await call_next(request)
    return response


@app.middleware("http")
async def circuit_breaker_middleware(request: Request, call_next):
    """
    熔断器中间件
    
    监控API服务健康状态，当服务出现故障时触发熔断器保护。
    
    Args:
        request: FastAPI请求对象
        call_next: 下一个中间件或路由处理函数
        
    Returns:
        Response: 响应对象
    """
    if not settings.CIRCUIT_BREAKER_ENABLED:
        return await call_next(request)
    
    try:
        response = await call_next(request)
        health_checker.report_health("api", healthy=True)
        return response
    except Exception as e:
        health_checker.report_health("api", healthy=False)
        raise


# 注册依赖覆盖
app.dependency_overrides[CompanyApplicationService] = get_company_service
app.dependency_overrides[JobApplicationService] = get_job_service
app.dependency_overrides[CandidateApplicationService] = get_candidate_service
app.dependency_overrides[MatchApplicationService] = get_match_service
app.dependency_overrides[ProcessApplicationService] = get_process_service
app.dependency_overrides[SearchApplicationService] = get_search_service


# 注册路由
app.include_router(api_router, prefix="/api/v1")
app.include_router(evaluation_router, prefix="/api/v1")
app.include_router(mcp_router)


# 启动事件
@app.on_event("startup")
async def startup_event():
    """
    应用启动事件处理
    
    初始化数据库并注册健康检查服务。
    """
    logger.info("Starting Job Agent service...")
    await init_db()
    logger.info("Database initialized successfully")
    
    # 注册健康检查服务
    health_checker.report_health("api", healthy=True)
    logger.info("Health checker initialized")


# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """
    应用关闭事件处理
    
    关闭数据库集群连接。
    """
    logger.info("Shutting down Job Agent service...")
    await db_cluster.close()
    logger.info("Database cluster closed")


# 健康检查接口
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    健康检查接口
    
    返回服务基本健康状态信息。
    
    Returns:
        Dict: 健康状态信息
    """
    db_health = db_cluster.health_check()
    return {
        "status": "healthy",
        "service": "jobagent",
        "database": db_health,
        "rate_limit_enabled": settings.RATE_LIMIT_ENABLED,
        "circuit_breaker_enabled": settings.CIRCUIT_BREAKER_ENABLED,
    }


@app.get("/health/details")
async def health_check_details():
    """
    详细健康检查接口
    
    返回数据库和各服务的详细健康状态。
    
    Returns:
        Dict: 详细健康状态信息
    """
    return {
        "status": "healthy" if all(
            db_health.get("healthy", True) for db_health in db_cluster.health_check().values()
        ) else "unhealthy",
        "database": db_cluster.health_check(),
        "services": health_checker.get_all_health_status(),
    }


# 应用入口
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
