
# Job Agent 系统 - 技术设计文档（TDD）

## 1. 文档概述

### 1.1 文档目的
本文档基于《Job Agent 系统 - 产品需求文档（PRD）》，详细描述系统的技术实现方案，包括架构设计、模块划分、数据库设计、API 接口设计、部署方案等，为开发团队提供完整的技术指导。

### 1.2 文档范围
- 系统整体架构设计
- 核心模块详细设计
- 数据库与数据结构设计
- API 接口设计
- 安全方案设计
- 部署与运维方案

### 1.3 技术选型

| 分类 | 技术 | 版本 | 选型理由 |
| :--- | :--- | :--- | :--- |
| 语言 | Python | 3.11+ | 生态成熟，支持 MCP 协议，适合 AI 应用开发 |
| 框架 | FastAPI | 0.100+ | 高性能异步框架，支持 OpenAPI 标准 |
| 数据库 | PostgreSQL | 16+ | 支持 JSON 类型，适合半结构化数据存储 |
| 缓存 | Redis | 7.0+ | 高性能缓存，支持分布式锁和消息队列 |
| MCP SDK | mcp-sdk | 0.10+ | 标准 MCP 协议支持 |
| 消息队列 | Redis Pub/Sub | - | 轻量级消息传递，适合 Agent 间通信 |
| 大模型 | OpenAI API / 国产大模型 | - | 支持语义匹配和自然语言处理 |

---

## 2. 系统架构设计

### 2.1 整体架构

```mermaid
graph TB
    subgraph 客户端层
        A[企业 Agent]
        B[求职者 Agent]
    end
    
    subgraph 接入层
        C[MCP 协议网关]
        D[API 网关]
    end
    
    subgraph 平台服务层
        E[匹配引擎服务]
        F[流程调度服务]
        G[安全管控服务]
        H[企业管理服务]
        I[候选人管理服务]
    end
    
    subgraph 数据层
        J[(PostgreSQL 主库)]
        K[(Redis 缓存)]
        L[(Elasticsearch)]
    end
    
    subgraph MCP 服务端层
        M[企业 MCP Server]
        N[候选人 MCP Server]
    end
    
    A --> C
    B --> C
    C --> E
    C --> F
    C --> G
    E --> J
    E --> K
    E --> L
    F --> J
    F --> K
    G --> J
    H --> J
    I --> J
    M --> C
    N --> C
```

### 2.2 架构分层说明

| 层级 | 名称 | 职责描述 | 关键组件 |
| :--- | :--- | :--- | :--- |
| 客户端层 | 企业/求职者 Agent | 发起请求、接收响应、展示结果 | 企业 HR Agent、候选人求职 Agent |
| 接入层 | MCP 协议网关 | 协议转换、请求路由、身份认证 | MCP Gateway、API Gateway |
| 平台服务层 | 核心服务集群 | 业务逻辑处理、流程编排 | 匹配引擎、流程调度、安全管控 |
| 数据层 | 数据存储 | 结构化数据存储、缓存、全文检索 | PostgreSQL、Redis、Elasticsearch |
| MCP 服务端层 | MCP Server | 封装企业/候选人系统接口 | 企业 MCP Server、候选人 MCP Server |

### 2.3 核心服务关系图

```mermaid
graph LR
    subgraph 匹配引擎服务
        A1[岗位画像构建]
        A2[候选人画像构建]
        A3[语义匹配算法]
        A4[匹配结果推送]
    end
    
    subgraph 流程调度服务
        B1[岗位同步]
        B2[简历推送]
        B3[初筛互动]
        B4[面试协调]
        B5[状态同步]
    end
    
    subgraph 安全管控服务
        C1[数据脱敏]
        C2[合规校验]
        C3[身份认证]
        C4[访问日志]
    end
    
    A1 --> A3
    A2 --> A3
    A3 --> A4
    B1 --> B2
    B2 --> B3
    B3 --> B4
    B4 --> B5
    C1 --> C2
    C2 --> C3
    C3 --> C4
    A4 --> B2
    B5 --> C4
```

---

## 3. 模块详细设计

### 3.1 MCP 协议网关模块

#### 3.1.1 功能职责
- MCP 协议解析与转换
- 请求路由与负载均衡
- 身份认证与授权
- 协议版本适配

#### 3.1.2 核心类设计

| 类名 | 职责 | 关键方法 |
| :--- | :--- | :--- |
| MCPGateway | MCP 协议网关主类 | `handle_request()`, `route_request()` |
| MCPProtocolParser | MCP 协议解析器 | `parse_mcp_request()`, `build_mcp_response()` |
| AuthMiddleware | 认证中间件 | `authenticate()`, `authorize()` |
| VersionAdapter | 版本适配器 | `adapt_request()`, `adapt_response()` |

#### 3.1.3 MCP 消息结构

```python
# MCP 请求消息结构
class MCPRequest:
    protocol_version: str        # 协议版本
    agent_id: str               # Agent 标识
    action: str                 # 操作类型
    payload: dict               # 请求载荷
    timestamp: int              # 时间戳
    signature: str              # 签名

# MCP 响应消息结构
class MCPResponse:
    status: str                 # 状态码
    data: dict                  # 响应数据
    message: str                # 响应消息
    timestamp: int              # 时间戳
```

### 3.2 匹配引擎服务

#### 3.2.1 功能职责
- 岗位画像构建与更新
- 候选人画像构建与更新
- 语义匹配算法执行
- 匹配结果排序与推送

#### 3.2.2 核心类设计

| 类名 | 职责 | 关键方法 |
| :--- | :--- | :--- |
| ProfileBuilder | 画像构建器 | `build_job_profile()`, `build_candidate_profile()` |
| MatchEngine | 匹配引擎 | `semantic_match()`, `weighted_scoring()` |
| ResultPusher | 结果推送器 | `push_to_company()`, `push_to_candidate()` |

#### 3.2.3 匹配算法流程

```mermaid
flowchart TD
    A[接收匹配请求] --> B[获取岗位画像]
    B --> C[获取候选人画像]
    C --> D[语义相似度计算]
    D --> E[权重因子计算]
    E --> F[综合得分计算]
    F --> G[TopN 排序]
    G --> H[生成匹配理由]
    H --> I[返回匹配结果]
```

#### 3.2.4 匹配权重配置

| 匹配维度 | 权重 | 说明 |
| :--- | :--- | :--- |
| 技能匹配 | 0.35 | 技能标签相似度 |
| 经验匹配 | 0.25 | 工作经验年限匹配 |
| 学历匹配 | 0.15 | 学历层次匹配 |
| 地点偏好 | 0.10 | 工作地点匹配 |
| 薪资期望 | 0.10 | 薪资范围匹配 |
| 岗位热度 | 0.05 | 岗位紧急程度 |

### 3.3 流程调度服务

#### 3.3.1 功能职责
- 招聘流程状态管理
- 流程节点调度
- 状态同步与通知
- 断点续聊支持

#### 3.3.2 状态机设计

```mermaid
stateDiagram-v2
    [*] --> JobPosted
    JobPosted --> ResumePushed: 匹配完成
    ResumePushed --> Screening: 简历推送成功
    Screening --> InterviewScheduled: 初筛通过
    Screening --> Rejected: 初筛拒绝
    InterviewScheduled --> Offer: 面试通过
    InterviewScheduled --> Rejected: 面试失败
    Offer --> Accepted: 候选人接受
    Offer --> Rejected: 候选人拒绝
    Accepted --> [*]
    Rejected --> [*]
```

#### 3.3.3 核心类设计

| 类名 | 职责 | 关键方法 |
| :--- | :--- | :--- |
| ProcessScheduler | 流程调度器 | `schedule_task()`, `execute_node()` |
| StateManager | 状态管理器 | `update_state()`, `get_state()` |
| EventBus | 事件总线 | `publish_event()`, `subscribe_event()` |

### 3.4 安全管控服务

#### 3.4.1 功能职责
- 敏感数据脱敏处理
- 违规内容检测
- 身份认证与授权
- 操作日志记录

#### 3.4.2 脱敏规则设计

| 数据类型 | 脱敏方式 | 示例 |
| :--- | :--- | :--- |
| 手机号 | 中间4位掩码 | 138****8888 |
| 邮箱 | @前1位后掩码 | a***@example.com |
| 姓名 | 姓+* | 张** |
| 身份证 | 前后各3位 | 110****1234 |
| 企业名称 | 关键词替换 | *科技有限公司 |

#### 3.4.3 合规检测规则

| 检测类型 | 规则描述 | 处理方式 |
| :--- | :--- | :--- |
| 虚假岗位 | 检测异常薪资、虚假公司信息 | 拦截并标记 |
| 违规内容 | 检测色情、暴力、政治敏感内容 | 过滤并告警 |
| 重复发布 | 检测相同岗位重复发布 | 合并或拒绝 |
| 敏感行业 | 检测金融诈骗、传销等行业 | 拒绝接入 |

---

## 4. 数据库设计

### 4.1 数据库表结构

#### 4.1.1 企业表（companies）

| 字段名 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | VARCHAR(36) | PRIMARY KEY | 企业唯一标识 |
| name | VARCHAR(255) | NOT NULL | 企业名称 |
| mcp_server_url | VARCHAR(500) | NOT NULL | MCP Server 地址 |
| api_key | VARCHAR(255) | NOT NULL | API 密钥 |
| status | VARCHAR(20) | DEFAULT 'active' | 状态：active/inactive |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

#### 4.1.2 岗位表（jobs）

| 字段名 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | VARCHAR(36) | PRIMARY KEY | 岗位唯一标识 |
| company_id | VARCHAR(36) | FOREIGN KEY | 企业标识 |
| title | VARCHAR(255) | NOT NULL | 岗位名称 |
| description | TEXT | - | 岗位描述 |
| requirements | TEXT | - | 任职要求 |
| location | VARCHAR(100) | - | 工作地点 |
| salary_range | VARCHAR(50) | - | 薪资范围 |
| tags | JSONB | - | 岗位标签 |
| status | VARCHAR(20) | DEFAULT 'open' | 状态：open/closed |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

#### 4.1.3 候选人表（candidates）

| 字段名 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | VARCHAR(36) | PRIMARY KEY | 候选人唯一标识 |
| mcp_server_url | VARCHAR(500) | NOT NULL | MCP Server 地址 |
| api_key | VARCHAR(255) | NOT NULL | API 密钥 |
| name | VARCHAR(100) | - | 姓名（脱敏） |
| phone | VARCHAR(20) | - | 手机号（脱敏） |
| email | VARCHAR(255) | - | 邮箱（脱敏） |
| resume_text | TEXT | - | 简历内容 |
| skills | JSONB | - | 技能标签 |
| experience | VARCHAR(100) | - | 工作经验 |
| education | VARCHAR(50) | - | 学历 |
| job_intent | JSONB | - | 求职意向 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

#### 4.1.4 匹配记录表（matches）

| 字段名 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | VARCHAR(36) | PRIMARY KEY | 匹配记录唯一标识 |
| job_id | VARCHAR(36) | FOREIGN KEY | 岗位标识 |
| candidate_id | VARCHAR(36) | FOREIGN KEY | 候选人标识 |
| score | DECIMAL(5,4) | NOT NULL | 匹配分数 |
| match_reasons | JSONB | - | 匹配理由 |
| status | VARCHAR(20) | DEFAULT 'pending' | 状态 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

#### 4.1.5 流程状态表（process_states）

| 字段名 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | VARCHAR(36) | PRIMARY KEY | 流程状态唯一标识 |
| match_id | VARCHAR(36) | FOREIGN KEY | 匹配记录标识 |
| current_state | VARCHAR(50) | NOT NULL | 当前状态 |
| history | JSONB | - | 状态变更历史 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

#### 4.1.6 访问日志表（access_logs）

| 字段名 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | BIGSERIAL | PRIMARY KEY | 日志唯一标识 |
| agent_id | VARCHAR(36) | NOT NULL | Agent 标识 |
| action | VARCHAR(100) | NOT NULL | 操作类型 |
| request_data | JSONB | - | 请求数据 |
| response_data | JSONB | - | 响应数据 |
| status_code | INT | NOT NULL | 状态码 |
| ip_address | VARCHAR(50) | - | IP 地址 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

### 4.2 索引设计

| 表名 | 索引名 | 字段 | 类型 |
| :--- | :--- | :--- | :--- |
| jobs | idx_jobs_company_id | company_id | BTREE |
| jobs | idx_jobs_status | status | BTREE |
| jobs | idx_jobs_tags | tags | GIN |
| candidates | idx_candidates_skills | skills | GIN |
| matches | idx_matches_job_id | job_id | BTREE |
| matches | idx_matches_candidate_id | candidate_id | BTREE |
| matches | idx_matches_score | score | BTREE |
| process_states | idx_process_match_id | match_id | BTREE |

---

## 5. API 接口设计

### 5.1 MCP 协议接口

#### 5.1.1 企业 MCP Server 接口规范

| 接口路径 | HTTP 方法 | 功能描述 |
| :--- | :--- | :--- |
| `/mcp/v1/company/jobs` | GET | 获取岗位列表 |
| `/mcp/v1/company/jobs/{job_id}` | GET | 获取岗位详情 |
| `/mcp/v1/company/search/resume` | POST | 搜索候选人简历 |
| `/mcp/v1/company/recruitment/status` | PUT | 更新招聘状态 |

##### `GET /mcp/v1/company/jobs`

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| filter | string | 否 | 过滤条件（JSON 格式） |
| page | int | 否 | 页码，默认 1 |
| size | int | 否 | 每页数量，默认 20 |

**响应示例：**
```json
{
    "status": "success",
    "data": {
        "jobs": [
            {
                "job_id": "uuid-xxx",
                "title": "高级 Python 工程师",
                "location": "北京",
                "salary_range": "20k-35k",
                "tags": ["Python", "Django", "Redis"]
            }
        ],
        "total": 100,
        "page": 1,
        "size": 20
    },
    "message": "获取成功"
}
```

##### `POST /mcp/v1/company/search/resume`

**请求体：**
```json
{
    "criteria": {
        "skills": ["Python", "FastAPI"],
        "experience": "3-5年",
        "education": "本科",
        "location": "北京"
    },
    "limit": 10
}
```

**响应示例：**
```json
{
    "status": "success",
    "data": {
        "candidates": [
            {
                "candidate_id": "uuid-xxx",
                "name": "张**",
                "skills": ["Python", "FastAPI", "Redis"],
                "experience": "4年",
                "education": "本科"
            }
        ]
    },
    "message": "搜索成功"
}
```

#### 5.1.2 候选人 MCP Server 接口规范

| 接口路径 | HTTP 方法 | 功能描述 |
| :--- | :--- | :--- |
| `/mcp/v1/candidate/profile` | GET | 获取候选人简历 |
| `/mcp/v1/candidate/job_intent` | PUT | 更新求职意向 |
| `/mcp/v1/candidate/apply` | POST | 申请岗位 |
| `/mcp/v1/candidate/status` | GET | 查询申请状态 |

##### `GET /mcp/v1/candidate/profile`

**响应示例：**
```json
{
    "status": "success",
    "data": {
        "candidate_id": "uuid-xxx",
        "name": "张**",
        "phone": "138****8888",
        "email": "z***@example.com",
        "skills": ["Python", "FastAPI", "PostgreSQL"],
        "experience": "4年",
        "education": "本科",
        "job_intent": {
            "position": "后端开发",
            "location": ["北京", "上海"],
            "salary_min": 20000,
            "salary_max": 35000
        }
    },
    "message": "获取成功"
}
```

### 5.2 平台内部 API

#### 5.2.1 匹配引擎 API

| 接口路径 | HTTP 方法 | 功能描述 |
| :--- | :--- | :--- |
| `/api/v1/match/job/{job_id}` | GET | 获取岗位匹配结果 |
| `/api/v1/match/candidate/{candidate_id}` | GET | 获取候选人匹配结果 |
| `/api/v1/match/batch` | POST | 批量匹配 |
| `/api/v1/match/{match_id}` | PUT | 更新匹配状态 |

#### 5.2.2 流程调度 API

| 接口路径 | HTTP 方法 | 功能描述 |
| :--- | :--- | :--- |
| `/api/v1/process/{match_id}/state` | GET | 获取流程状态 |
| `/api/v1/process/{match_id}/transition` | POST | 流程状态转换 |
| `/api/v1/process/{match_id}/history` | GET | 获取流程历史 |

#### 5.2.3 管理后台 API

| 接口路径 | HTTP 方法 | 功能描述 |
| :--- | :--- | :--- |
| `/api/v1/admin/companies` | GET/POST | 企业管理 |
| `/api/v1/admin/companies/{company_id}` | GET/PUT/DELETE | 企业详情与操作 |
| `/api/v1/admin/jobs` | GET | 岗位列表 |
| `/api/v1/admin/candidates` | GET | 候选人列表 |
| `/api/v1/admin/logs` | GET | 访问日志查询 |

---

## 6. 安全设计

### 6.1 身份认证方案

```mermaid
sequenceDiagram
    participant Agent as 企业/候选人 Agent
    participant Gateway as MCP 网关
    participant Auth as 认证服务
    participant DB as 数据库
    
    Agent->>Gateway: 请求（携带 API Key）
    Gateway->>Auth: 验证 API Key
    Auth->>DB: 查询 Agent 信息
    DB-->>Auth: 返回 Agent 记录
    alt API Key 有效
        Auth-->>Gateway: 认证成功（返回 Agent ID）
        Gateway->>Gateway: 路由到对应服务
        Gateway-->>Agent: 响应请求
    else API Key 无效
        Auth-->>Gateway: 认证失败
        Gateway-->>Agent: 401 Unauthorized
    end
```

### 6.2 数据加密方案

| 加密层次 | 加密方式 | 应用场景 |
| :--- | :--- | :--- |
| 传输层 | TLS 1.3 | 所有 API 通信 |
| 存储层 | AES-256 | 敏感字段加密存储 |
| 数据库 | Transparent Data Encryption | PostgreSQL TDE |

### 6.3 访问控制策略

| 角色 | 权限范围 |
| :--- | :--- |
| 企业管理员 | 管理企业信息、查看岗位、筛选简历 |
| 招聘专员 | 发布岗位、查看匹配候选人、发起面试 |
| 候选人 | 查看岗位推荐、申请岗位、查询状态 |
| 平台管理员 | 全系统管理、配置、监控 |

---

## 7. 部署与集成方案

### 7.1 部署架构

```mermaid
graph TB
    subgraph 负载均衡层
        A[Nginx Load Balancer]
    end
    
    subgraph 应用层
        B[MCP Gateway]
        C[匹配引擎服务]
        D[流程调度服务]
        E[安全管控服务]
    end
    
    subgraph 数据层
        F[(PostgreSQL)]
        G[(Redis Cluster)]
        H[(Elasticsearch)]
    end
    
    subgraph 监控层
        I[Prometheus]
        J[Grafana]
        K[ELK Stack]
    end
    
    A --> B
    A --> C
    A --> D
    A --> E
    B --> F
    B --> G
    C --> F
    C --> G
    C --> H
    D --> F
    D --> G
    E --> F
    E --> G
    I --> B
    I --> C
    I --> D
    I --> E
    J --> I
    K --> B
    K --> C
    K --> D
    K --> E
```

### 7.2 Docker 容器配置

#### 7.2.1 docker-compose.yml 关键配置

```yaml
version: '3.8'

services:
  mcp-gateway:
    build: ./mcp-gateway
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/jobagent
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis

  match-engine:
    build: ./match-engine
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/jobagent
      - REDIS_URL=redis://redis:6379
      - ES_URL=http://elasticsearch:9200
    depends_on:
      - postgres
      - redis
      - elasticsearch

  process-scheduler:
    build: ./process-scheduler
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/jobagent
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis

  security-service:
    build: ./security-service
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/jobagent
    depends_on:
      - postgres

  postgres:
    image: postgres:16
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=jobagent

  redis:
    image: redis:7
    volumes:
      - redis_data:/data

  elasticsearch:
    image: elasticsearch:8
    volumes:
      - es_data:/usr/share/elasticsearch/data
    environment:
      - discovery.type=single-node

volumes:
  postgres_data:
  redis_data:
  es_data:
```

### 7.3 CI/CD 流程

```mermaid
flowchart TD
    A[代码提交] --> B[GitHub Actions]
    B --> C[代码检查]
    C --> D[单元测试]
    D --> E[构建 Docker 镜像]
    E --> F[镜像推送]
    F --> G[部署到测试环境]
    G --> H[集成测试]
    H --> I{测试通过?}
    I -->|是| J[部署到生产环境]
    I -->|否| K[反馈修复]
    K --> A
```

---

## 8. 性能优化方案

### 8.1 缓存策略

| 缓存类型 | 缓存内容 | 过期时间 | 缓存策略 |
| :--- | :--- | :--- | :--- |
| 岗位列表 | 企业岗位列表 | 5 分钟 | 定时刷新 + 事件驱动刷新 |
| 候选人画像 | 候选人技能、经验等 | 10 分钟 | LRU 淘汰 |
| 匹配结果 | TopN 匹配结果 | 30 分钟 | 缓存优先，异步更新 |
| 热点数据 | 高频访问的岗位/候选人 | 1 小时 | 预热缓存 |

### 8.2 异步处理

| 场景 | 处理方式 | 队列类型 |
| :--- | :--- | :--- |
| 批量匹配 | 异步任务队列 | Redis Queue |
| 结果推送 | 延迟推送 | Redis Pub/Sub |
| 画像更新 | 异步更新 | Celery |

### 8.3 数据库优化

| 优化策略 | 应用场景 | 预期效果 |
| :--- | :--- | :--- |
| 读写分离 | 高读低写场景 | 提升读性能 2-3 倍 |
| 分库分表 | 数据量达千万级 | 降低单表压力 |
| 查询缓存 | 热点查询 | 减少数据库访问 |
| 索引优化 | 复杂查询 | 提升查询速度 |

---

## 9. 监控与日志

### 9.1 监控指标

| 指标类型 | 监控项 | 告警阈值 |
| :--- | :--- | :--- |
| 服务指标 | 请求响应时间 | > 3s |
| 服务指标 | 错误率 | > 5% |
| 服务指标 | QPS | > 1000 |
| 数据库指标 | 查询响应时间 | > 500ms |
| 数据库指标 | 连接数 | > 80% |
| 缓存指标 | 命中率 | < 90% |
| 系统指标 | CPU 使用率 | > 80% |
| 系统指标 | 内存使用率 | > 85% |

### 9.2 日志结构

```json
{
    "timestamp": "2024-01-15T10:30:00Z",
    "level": "INFO",
    "service": "match-engine",
    "request_id": "uuid-xxx",
    "agent_id": "company-abc",
    "action": "semantic_match",
    "status": "success",
    "duration_ms": 1250,
    "data": {
        "job_id": "job-123",
        "candidate_count": 100,
        "matched_count": 10
    },
    "error": null
}
```

---

## 10. 代码安全性

### 10.1 注意事项

| 风险类型 | 风险描述 | 关联模块 |
| :--- | :--- | :--- |
| 注入攻击 | SQL 注入、命令注入 | 数据库访问层 |
| 数据泄露 | 敏感数据明文存储 | 数据存储层 |
| 身份伪造 | 恶意 Agent 冒充 | 认证模块 |
| 拒绝服务 | 大量请求导致服务不可用 | 网关层 |
| 协议漏洞 | MCP 协议实现缺陷 | MCP 网关 |

### 10.2 解决方案

| 风险类型 | 解决方案 | 实施位置 |
| :--- | :--- | :--- |
| 注入攻击 | 使用 ORM 参数化查询，禁止拼接 SQL | 所有数据库操作 |
| 数据泄露 | 敏感字段加密存储，传输加密 | 数据层、传输层 |
| 身份伪造 | API Key + 签名验证，定期轮换密钥 | 认证模块 |
| 拒绝服务 | 限流熔断，请求频率限制 | 网关层、服务层 |
| 协议漏洞 | 使用成熟 MCP SDK，定期安全审计 | MCP 网关 |

---

## 11. 附录

### 11.1 版本历史

| 版本 | 日期 | 修改内容 | 作者 |
| :--- | :--- | :--- | :--- |
| v1.0 | 2026-06-12 | 初始版本 | Tech Team |

### 11.2 参考文档

- 《Job Agent 系统 - 产品需求文档（PRD）》
- MCP 协议规范 v1.0
- FastAPI 官方文档
- PostgreSQL 最佳实践

