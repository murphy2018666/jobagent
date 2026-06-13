from typing import Tuple, List, Dict, Any, Optional
from loguru import logger
from ..domain.services import SecurityService
from cryptography.fernet import Fernet
from jose import JWTError, jwt
from datetime import datetime, timedelta
import re


class SecurityServiceImpl(SecurityService):
    """
    安全服务实现
    
    提供数据加密、脱敏、内容验证等安全相关功能。
    """
    
    def __init__(self, secret_key: str):
        """
        初始化安全服务
        
        Args:
            secret_key: 加密密钥，用于Fernet对称加密
        """
        self.cipher = Fernet(secret_key)
        self.forbidden_patterns = [
            r"(?i)色情|低俗|暴力|赌博|诈骗|传销",
            r"(?i)虚假岗位|高薪诚聘.*无需经验",
            r"(?i)刷单|兼职.*日结.*轻松",
            r"(?i)敏感政治内容|违法",
        ]

    def encrypt_data(self, data: str) -> str:
        """
        加密数据
        
        使用Fernet对称加密算法对字符串数据进行加密。
        
        Args:
            data: 待加密的数据
            
        Returns:
            str: 加密后的数据
            
        Raises:
            Exception: 加密失败时记录日志并返回原始数据
        """
        try:
            return self.cipher.encrypt(data.encode()).decode()
        except Exception as e:
            logger.error(f"Encryption error: {str(e)}")
            return data

    def decrypt_data(self, encrypted_data: str) -> str:
        """
        解密数据
        
        使用Fernet对称加密算法对加密数据进行解密。
        
        Args:
            encrypted_data: 加密的数据
            
        Returns:
            str: 解密后的数据
            
        Raises:
            Exception: 解密失败时记录日志并返回原始数据
        """
        try:
            return self.cipher.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logger.error(f"Decryption error: {str(e)}")
            return encrypted_data

    def mask_phone(self, phone: str) -> str:
        """
        手机号脱敏
        
        对手机号进行脱敏处理，中间4位用*代替。
        
        Args:
            phone: 原始手机号
            
        Returns:
            str: 脱敏后的手机号，如138****1234
        """
        if len(phone) >= 11:
            return phone[:3] + "****" + phone[-4:]
        return "***"

    def mask_email(self, email: str) -> str:
        """
        邮箱脱敏
        
        对邮箱地址进行脱敏处理，用户名部分只保留首字母。
        
        Args:
            email: 原始邮箱地址
            
        Returns:
            str: 脱敏后的邮箱，如a***@example.com
        """
        match = re.match(r"^(.?)[^@]*@(.+)$", email)
        if match:
            return f"{match.group(1)}***@{match.group(2)}"
        return "***@***.com"

    def mask_name(self, name: str) -> str:
        """
        姓名脱敏
        
        对姓名进行脱敏处理，只保留首字符。
        
        Args:
            name: 原始姓名
            
        Returns:
            str: 脱敏后的姓名，如张**
        """
        if len(name) >= 2:
            return name[0] + "**"
        return "*"

    def validate_content(self, content: str) -> Tuple[bool, List[str]]:
        """
        内容安全验证
        
        检查内容是否包含违规信息，如色情、暴力、诈骗等内容。
        
        Args:
            content: 待验证的内容
            
        Returns:
            Tuple[bool, List[str]]: 验证结果和违规信息列表
                - bool: True表示内容合法，False表示包含违规内容
                - List[str]: 违规信息列表，为空表示内容合法
        """
        violations = []
        for pattern in self.forbidden_patterns:
            if re.search(pattern, content):
                violations.append(f"包含违规内容: {pattern}")
        
        if violations:
            return False, violations
        return True, []


class JWTService:
    """
    JWT服务
    
    提供JWT令牌的创建和验证功能。
    """
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        """
        初始化JWT服务
        
        Args:
            secret_key: JWT签名密钥
            algorithm: 签名算法，默认为HS256
        """
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        创建访问令牌
        
        Args:
            data: 令牌载荷数据
            expires_delta: 过期时间差，默认为15分钟
            
        Returns:
            str: JWT访问令牌
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证令牌
        
        验证JWT令牌的有效性并解码载荷。
        
        Args:
            token: JWT令牌
            
        Returns:
            Optional[Dict[str, Any]]: 解码后的载荷数据，验证失败返回None
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None


class AuthMiddleware:
    """
    认证中间件
    
    提供API密钥和JWT令牌的认证功能，支持企业和候选人两种身份类型。
    """
    
    def __init__(self, company_repo, candidate_repo, jwt_service: JWTService):
        """
        初始化认证中间件
        
        Args:
            company_repo: 企业仓储实例
            candidate_repo: 候选人仓储实例
            jwt_service: JWT服务实例
        """
        self.company_repo = company_repo
        self.candidate_repo = candidate_repo
        self.jwt_service = jwt_service

    async def authenticate(self, api_key: Optional[str] = None, token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        认证用户
        
        支持通过API密钥或JWT令牌进行认证。
        
        Args:
            api_key: API密钥
            token: JWT令牌
            
        Returns:
            Optional[Dict[str, Any]]: 认证成功返回用户信息，失败返回None
                - type: 用户类型（company/candidate）
                - id: 用户ID
                - entity: 用户实体对象
        """
        if api_key:
            company = await self.company_repo.get_by_api_key(api_key)
            if company:
                return {"type": "company", "id": company.id, "entity": company}
            
            candidate = await self.candidate_repo.get_by_api_key(api_key)
            if candidate:
                return {"type": "candidate", "id": candidate.id, "entity": candidate}
        
        if token:
            payload = self.jwt_service.verify_token(token)
            if payload:
                return {"type": payload.get("type"), "id": payload.get("sub"), "entity": None}
        
        return None

    async def authorize(self, credentials: Dict[str, Any], required_role: str) -> bool:
        """
        授权检查
        
        检查用户是否具有指定角色的访问权限。
        
        Args:
            credentials: 用户认证信息
            required_role: 所需角色
            
        Returns:
            bool: 具有权限返回True，否则返回False
        """
        role_mapping = {
            "company": ["company", "admin"],
            "candidate": ["candidate", "admin"],
            "admin": ["admin"],
        }
        
        user_type = credentials.get("type")
        return required_role in role_mapping.get(user_type, [])
