import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from loguru import logger
from ..domain.services import McpProtocolService
from ..domain.repositories import CompanyRepository, CandidateRepository
from ..config.settings import settings


class McpProtocolServiceImpl(McpProtocolService):
    """
    MCP协议服务实现
    
    实现企业和候选人通过MCP协议接入平台的标准化协议，支持跨平台Agent互联。
    """
    
    def __init__(self, company_repo: CompanyRepository, candidate_repo: CandidateRepository):
        """
        初始化MCP协议服务
        
        Args:
            company_repo: 企业仓储实例
            candidate_repo: 候选人仓储实例
        """
        self.company_repo = company_repo
        self.candidate_repo = candidate_repo
        self.timeout = aiohttp.ClientTimeout(total=settings.MCP_TIMEOUT_SECONDS)

    async def call_company_mcp(self, company_id: str, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用企业MCP接口
        
        Args:
            company_id: 企业ID
            action: 操作类型
            payload: 请求负载
            
        Returns:
            Dict[str, Any]: MCP响应结果
            
        Raises:
            ValueError: 企业不存在时抛出
        """
        company = await self.company_repo.get_by_id(company_id)
        if not company:
            raise ValueError("Company not found")
        
        url = f"{company.mcp_server_url}/mcp/{settings.MCP_PROTOCOL_VERSION}/company/{action}"
        headers = {"Authorization": f"Bearer {company.api_key}"}
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"MCP call failed: {response.status}")
                        return {"status": "error", "message": f"HTTP {response.status}"}
        except Exception as e:
            logger.error(f"MCP call error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def call_candidate_mcp(self, candidate_id: str, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用候选人MCP接口
        
        Args:
            candidate_id: 候选人ID
            action: 操作类型
            payload: 请求负载
            
        Returns:
            Dict[str, Any]: MCP响应结果
            
        Raises:
            ValueError: 候选人不存在时抛出
        """
        candidate = await self.candidate_repo.get_by_id(candidate_id)
        if not candidate:
            raise ValueError("Candidate not found")
        
        url = f"{candidate.mcp_server_url}/mcp/{settings.MCP_PROTOCOL_VERSION}/candidate/{action}"
        headers = {"Authorization": f"Bearer {candidate.api_key}"}
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"MCP call failed: {response.status}")
                        return {"status": "error", "message": f"HTTP {response.status}"}
        except Exception as e:
            logger.error(f"MCP call error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def fetch_job_list(self, company_id: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        从企业MCP服务器获取岗位列表
        
        Args:
            company_id: 企业ID
            filters: 过滤条件
            
        Returns:
            List[Dict[str, Any]]: 岗位列表
        """
        result = await self.call_company_mcp(company_id, "get_job_list", filters or {})
        if result.get("status") == "success":
            return result.get("data", {}).get("jobs", [])
        return []

    async def fetch_candidate_profile(self, candidate_id: str) -> Dict[str, Any]:
        """
        从候选人MCP服务器获取简历信息
        
        Args:
            candidate_id: 候选人ID
            
        Returns:
            Dict[str, Any]: 简历信息
        """
        result = await self.call_candidate_mcp(candidate_id, "get_profile", {})
        if result.get("status") == "success":
            return result.get("data", {})
        return {}


class McpRequest:
    """
    MCP请求对象
    
    封装MCP协议的请求数据结构。
    """
    
    def __init__(
        self,
        protocol_version: str,
        agent_id: str,
        action: str,
        payload: Dict[str, Any],
        timestamp: Optional[int] = None,
        signature: Optional[str] = None,
    ):
        """
        初始化MCP请求
        
        Args:
            protocol_version: 协议版本
            agent_id: Agent ID
            action: 操作类型
            payload: 请求负载
            timestamp: 请求时间戳
            signature: 请求签名
        """
        self.protocol_version = protocol_version
        self.agent_id = agent_id
        self.action = action
        self.payload = payload
        self.timestamp = timestamp
        self.signature = signature

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            Dict[str, Any]: 请求字典
        """
        return {
            "protocol_version": self.protocol_version,
            "agent_id": self.agent_id,
            "action": self.action,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "signature": self.signature,
        }


class McpResponse:
    """
    MCP响应对象
    
    封装MCP协议的响应数据结构。
    """
    
    def __init__(
        self,
        status: str,
        data: Dict[str, Any],
        message: str,
        timestamp: Optional[int] = None,
    ):
        """
        初始化MCP响应
        
        Args:
            status: 响应状态（success/error）
            data: 响应数据
            message: 响应消息
            timestamp: 响应时间戳
        """
        self.status = status
        self.data = data
        self.message = message
        self.timestamp = timestamp

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            Dict[str, Any]: 响应字典
        """
        return {
            "status": self.status,
            "data": self.data,
            "message": self.message,
            "timestamp": self.timestamp,
        }


class McpGateway:
    """
    MCP网关
    
    统一处理MCP协议请求，路由到对应的企业或候选人MCP服务。
    """
    
    def __init__(self, mcp_service: McpProtocolService):
        """
        初始化MCP网关
        
        Args:
            mcp_service: MCP协议服务实例
        """
        self.mcp_service = mcp_service

    async def handle_request(self, request: McpRequest) -> McpResponse:
        """
        处理MCP请求
        
        根据action前缀路由到对应的MCP服务：
        - company_开头的操作路由到企业MCP服务
        - candidate_开头的操作路由到候选人MCP服务
        
        Args:
            request: MCP请求对象
            
        Returns:
            McpResponse: MCP响应对象
        """
        try:
            if request.action.startswith("company_"):
                action = request.action.replace("company_", "")
                result = await self.mcp_service.call_company_mcp(request.agent_id, action, request.payload)
            elif request.action.startswith("candidate_"):
                action = request.action.replace("candidate_", "")
                result = await self.mcp_service.call_candidate_mcp(request.agent_id, action, request.payload)
            else:
                return McpResponse(
                    status="error",
                    data={},
                    message="Unknown action type"
                )
            
            return McpResponse(
                status=result.get("status", "success"),
                data=result.get("data", {}),
                message=result.get("message", "Success")
            )
        except Exception as e:
            logger.error(f"MCP gateway error: {str(e)}")
            return McpResponse(
                status="error",
                data={},
                message=str(e)
            )
