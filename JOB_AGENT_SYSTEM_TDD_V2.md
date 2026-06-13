
# Job Agent 系统 - 技术设计文档（TDD）v2.0

## 1. 文档概述

### 1.1 文档目的
本文档基于《Job Agent 系统 - 产品需求文档（PRD）》，详细描述系统的技术实现方案，包括架构设计、模块划分、数据库设计、API 接口设计、部署方案、高并发和分布式设计等，为开发团队提供完整的技术指导。

### 1.2 文档范围
- 系统整体架构设计
- 核心模块详细设计
- 数据库与数据结构设计
- API 接口设计
- 安全方案设计
- 高并发与分布式设计
- 部署与运维方案

### 1.3 技术选型

| 分类 | 技术 | 版本 | 选型理由 |
| :--- | :--- | :--- | :--- |
| 语言 | Python | 3.11+ | 生态成熟，支持 MCP 协议，适合 AI 应用开发 |
| 框架 | FastAPI | 0.100+ | 高性能异步框架，支持 OpenAPI 标准 |
| 数据库 | PostgreSQL | 16+ | 支持 JSON 类型，适合半结构化数据存储 |
| 缓存 | Redis | 7.0+ | 高性能缓存，支持分布式锁和消息队列 |
| 任务队列 | Celery | 5.3+ | 分布式任务调度，支持异步处理 |
| MCP SDK | mcp-sdk | 0.10+ | 标准 MCP 协议支持 |
| 消息队列 | Redis Pub/Sub | - | 轻量级消息传递，适合 Agent 间通信 |
| 大模型 | OpenAI API / 国产大模型 | - | 支持语义匹配和自然语言处理 |

---

## 2. 系统架构设计

### 2.1 整体架构（分布式版本）

```mermaid
graph TB
    subgraph 客户端层
        A[企业 Agent]
        B[求职者 Agent]
    end
    
    subgraph 负载均衡层
        C[Nginx / LB]
    end
    
    subgraph 接入层
        D[MCP 协议网关]
        E[API 网关]
    end
    
    subgraph 平台服务层
        F[匹配引擎服务]
        G[流程调度服务]
        H[安全管控服务]
        I[企业管理服务]
        J[候选人管理服务]
    end
    
    subgraph 异步任务层
        K[Celery Worker]
        L[任务队列 Redis]
    end
    
    subgraph 数据层
        M[(PostgreSQL 主库)]
        N[(PostgreSQL 从库1)]
        O[(PostgreSQL 从库2)]
        P[(Redis Cluster)]
        Q[(Elasticsearch)]
    end
    
    subgraph MCP 服务端层
        R[企业 MCP Server]
        S[候选人 MCP Server]
    end
    
    A --> C
    B --> C
    C --> D
    C --> E
    D --> F
    D --> G
    D --> H
    E --> I
    E --> J
    F --> L
    G --> L
    K --> L
    F --> M
    F --> N
    G --> M
    H --> M
    I --> N
    J --> O
    F --> P
    G --> P
    F --> Q
    R --> D
    S --> D
```

### 2.2 架构分层说明

| 层级 | 名称 | 职责描述 | 关键组件 |
| :--- | :--- | :--- | :--- |
| 客户端层 | 企业/求职者 Agent | 发起请求、接收响应、展示结果 | 企业 HR Agent、候选人求职 Agent |
| 负载均衡层 | 负载均衡器 | 请求分发、健康检查、故障转移 | Nginx、HAProxy |
| 接入层 | MCP 协议网关 | 协议转换、请求路由、身份认证、限流熔断 | MCP Gateway、API Gateway |
| 平台服务层 | 核心服务集群 | 业务逻辑处理、流程编排 | 匹配引擎、流程调度、安全管控 |
| 异步任务层 | 任务队列 | 异步任务调度、延迟任务、定时任务 | Celery、Redis |
| 数据层 | 数据存储 | 结构化数据存储、缓存、全文检索 | PostgreSQL 主从、Redis Cluster、Elasticsearch |
| MCP 服务端层 | MCP Server | 封装企业/候选人系统接口 | 企业 MCP Server、候选人 MCP Server |

---

## 3. 高并发与分布式设计

### 3.1 分布式架构设计

#### 3.1.1 服务集群化
- **水平扩展**：所有服务支持无状态水平扩展
- **服务发现**：使用 Consul 或 etcd 进行服务注册与发现
- **负载均衡**：轮询 + 最小连接数策略

#### 3.1.2 数据库读写分离

| 角色 | 用途 | 配置 |
| :--- | :--- | :--- |
| 主库 | 写操作 | 1 个主库 |
| 从库 | 读操作 | 2+ 个从库 |
| 连接池 | 连接管理 | 主库 20 连接，从库各 15 连接 |

#### 3.1.3 Redis Cluster

```mermaid
graph LR
    subgraph Redis Cluster
        A[Master 0]
        B[Master 1]
        C[Master 2]
        D[Slave 0-1]
        E[Slave 1-1]
        F[Slave 2-1]
    end
    
    A --> D
    B --> E
    C --> F
```

### 3.2 异步任务处理

#### 3.2.1 任务队列架构

| 队列名称 | 用途 | 优先级 |
| :--- | :--- | :--- |
| `match_queue` | 匹配任务 | 高 |
| `sync_queue` | 数据同步任务 | 中 |
| `notify_queue` | 通知任务 | 中 |
| `cleanup_queue` | 清理任务 | 低 |

#### 3.2.2 Celery 配置

```python
# 并发配置
worker_concurrency = 8
worker_prefetch_multiplier = 1
worker_max_tasks_per_child = 1000

# 任务超时
task_time_limit = 300
task_soft_time_limit = 240

# 定时任务
beat_schedule = {
    "cleanup-expired-matches": {
        "task": "cleanup_expired_matches",
        "schedule": crontab(hour=3, minute=0),
    },
}
```

### 3.3 分布式锁与 ID 生成

#### 3.3.1 分布式锁实现

```python
class DistributedLock:
    def __init__(self, client, timeout=10, wait_timeout=30):
        self.client = client
        self.timeout = timeout
        self.wait_timeout = wait_timeout
    
    @contextmanager
    def acquire(self, lock_key):
        identifier = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            while time.time() - start_time < self.wait_timeout:
                # SET NX 获取锁
                result = self.client.set(lock_key, identifier, ex=self.timeout, nx=True)
                if result:
                    yield True
                    return
                time.sleep(0.1)
            yield False
        finally:
            # 只能释放自己的锁
            current = self.client.get(lock_key)
            if current and current.decode() == identifier:
                self.client.delete(lock_key)
```

#### 3.3.2 分布式 ID 生成

采用类似 Snowflake 的 ID 生成方案：

| 组成部分 | 位数 | 说明 |
| :--- | :--- | :--- |
| 时间戳 | 41 位 | 毫秒级时间戳 |
| 数据中心 ID | 5 位 | 最多 32 个数据中心 |
| 工作节点 ID | 5 位 | 最多 32 个工作节点 |
| 序列号 | 12 位 | 每毫秒最多 4096 个 ID |

### 3.4 限流与熔断

#### 3.4.1 限流策略

| 限流类型 | 实现方式 | 参数配置 |
| :--- | :--- | :--- |
| IP 限流 | Redis 计数器 | 100 请求/分钟 |
| 用户限流 | Redis 计数器 | 50 请求/分钟 |
| 接口限流 | Redis 计数器 | 500 请求/分钟 |

#### 3.4.2 熔断器配置

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=30, half_open_max=3):
        self.failure_threshold = failure_threshold      # 失败阈值
        self.recovery_timeout = recovery_timeout       # 恢复超时时间
        self.half_open_max = half_open_max             # 半开状态最大请求数
    
    def call(self, service, func, *args, **kwargs):
        state = self._get_state(service)
        
        if state == "open":
            if self._should_attempt_reset(service):
                self._set_state(service, "half_open")
            else:
                raise CircuitBreakerError(f"Service {service} is unavailable")
        
        # 半开状态限制请求
        if state == "half_open" and self._is_limit_reached(service):
            raise CircuitBreakerError(f"Service {service} is in recovery")
        
        try:
            result = func(*args, **kwargs)
            # 成功，重置熔断器
            self._reset(service)
            return result
        except Exception as e:
            # 失败，增加计数
            self._record_failure(service)
            if self._should_open(service):
                self._set_state(service, "open")
            raise
```

#### 3.4.3 熔断器状态转换

```mermaid
stateDiagram-v2
    [*] --> Closed
    Closed --> Open: 失败次数 >= 阈值
    Open --> HalfOpen: 超时时间到达
    HalfOpen --> Closed: 请求成功
    HalfOpen --> Open: 请求失败
    Closed --> [*]
```

### 3.5 缓存策略

#### 3.5.1 多级缓存架构

```mermaid
graph LR
    A[请求] --> B[本地缓存]
    B -->|未命中| C[Redis 缓存]
    C -->|未命中| D[数据库]
    D --> C
    C --> B
    B --> A
```

#### 3.5.2 缓存配置

| 缓存类型 | TTL | 失效策略 |
| :--- | :--- | :--- |
| 岗位列表 | 5 分钟 | 事件驱动刷新 |
| 候选人画像 | 10 分钟 | LRU 淘汰 |
| 匹配结果 | 30 分钟 | 缓存优先，异步更新 |
| 热点数据 | 1 小时 | 预热缓存 |

### 3.6 数据分片设计

#### 3.6.1 分片策略

| 分片维度 | 分片键 | 分片数量 |
| :--- | :--- | :--- |
| 企业数据 | company_id | 4 |
| 候选人数据 | candidate_id | 8 |
| 匹配数据 | match_id | 16 |

#### 3.6.2 分片路由

```python
class ShardingRouter:
    def __init__(self, shard_count=4):
        self.shard_count = shard_count
    
    def get_shard_id(self, entity_id):
        hash_value = hashlib.md5(entity_id.encode()).hexdigest()
        return int(hash_value, 16) % self.shard_count
```

---

## 4. 核心模块设计

### 4.1 MCP 协议网关模块

#### 4.1.1 功能职责
- MCP 协议解析与转换
- 请求路由与负载均衡
- 身份认证与授权
- 协议版本适配

#### 4.1.2 MCP 消息结构

```python
class MCPRequest:
    protocol_version: str        # 协议版本
    agent_id: str               # Agent 标识
    action: str                 # 操作类型
    payload: dict               # 请求载荷
    timestamp: int              # 时间戳
    signature: str              # 签名

class MCPResponse:
    status: str                 # 状态码
    data: dict                  # 响应数据
    message: str                # 响应消息
    timestamp: int              # 时间戳
```

### 4.2 匹配引擎服务

#### 4.2.1 匹配算法流程

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

#### 4.2.2 匹配权重配置

| 匹配维度 | 权重 | 说明 |
| :--- | :--- | :--- |
| 技能匹配 | 0.35 | 技能标签相似度 |
| 经验匹配 | 0.25 | 工作经验年限匹配 |
| 学历匹配 | 0.15 | 学历层次匹配 |
| 地点偏好 | 0.10 | 工作地点匹配 |
| 薪资期望 | 0.10 | 薪资范围匹配 |
| 岗位热度 | 0.05 | 岗位紧急程度 |

### 4.3 评价模块服务

#### 4.3.1 企业评价模型

采用四大经典管理分析模型对企业进行综合评价：

| 评价维度 | 模型 | 特点 |
| :--- | :--- | :--- |
| 企业整体综合竞争力 | 麦肯锡7S模型 | 覆盖全维度，无遗漏 |
| 生命周期划分 | Dickinson现金流模型 | 基于公开数据，无主观偏差 |
| 财务盈利质量拆解 | 杜邦分析模型 | 逻辑清晰，可跨企业对比 |
| 行业竞争地位评价 | 波特五力模型 | 清晰定位护城河，判断长期价值 |

##### 4.3.1.1 麦肯锡7S模型

| 维度 | 权重 | 评价内容 |
| :--- | :--- | :--- |
| 战略 (Strategy) | 0.20 | 企业愿景、市场定位、竞争优势 |
| 结构 (Structure) | 0.12 | 组织架构、汇报关系、决策效率 |
| 制度 (Systems) | 0.12 | 管理制度、流程标准化、信息系统 |
| 共同价值观 (Shared Values) | 0.18 | 企业文化、核心价值观、员工认同 |
| 风格 (Style) | 0.10 | 领导风格、管理方式、创新氛围 |
| 员工 (Staff) | 0.14 | 人才质量、发展机制、团队稳定 |
| 技能 (Skills) | 0.14 | 核心能力、技术水平、创新能力 |

##### 4.3.1.2 Dickinson现金流模型

基于经营、投资、融资三类现金流的组合判断企业生命周期：

| 现金流组合 | 生命周期阶段 | 特征描述 |
| :--- | :--- | :--- |
| 经营>0, 投资<0, 融资>0 | 导入期-扩张型 | 新兴企业，积极扩张 |
| 经营>0, 投资<0, 融资<0 | 导入期-稳健型 | 稳健经营，自给自足 |
| 经营>0, 投资<0, 融资<0 | 成长期 | 主营业务盈利，持续投资 |
| 经营>0, 投资<0, 融资<0 | 成熟期 | 盈利稳定，投资减缓 |
| 经营<0, 投资>0, 融资>0 | 衰退期-挣扎型 | 主营业务亏损，转型投资 |
| 经营<0, 投资>0, 融资<0 | 衰退期-收缩型 | 收缩业务，偿还债务 |

##### 4.3.1.3 杜邦分析模型

| 分析维度 | 指标 | 计算公式 | 评分权重 |
| :--- | :--- | :--- | :--- |
| 盈利能力 | 净利率 | 净利润/营业收入 | 0.40 |
| | 毛利率 | (收入-成本)/收入 | - |
| | 营业利润率 | 营业利润/营业收入 | - |
| 经营效率 | 资产周转率 | 营业收入/总资产 | 0.30 |
| 财务健康 | 资产负债率 | 负债/总资产 | 0.30 |
| | 流动比率 | 流动资产/流动负债 | - |
| | 速动比率 | (流动资产-存货)/流动负债 | - |

##### 4.3.1.4 波特五力模型

| 五力 | 评价内容 | 权重 |
| :--- | :--- | :--- |
| 新进入者威胁 | 行业壁垒、规模经济、品牌忠诚度 | 0.20 |
| 供应商议价能力 | 供应商集中度、转换成本、前向整合能力 | 0.15 |
| 购买者议价能力 | 购买者集中度、转换成本、产品差异化 | 0.15 |
| 替代品威胁 | 替代品可用性、替代品性价比 | 0.20 |
| 行业内竞争 | 竞争对手数量、行业增长率、市场份额 | 0.30 |

#### 4.3.2 候选人评价模型

采用"双Agent协同评价模型"，兼顾效率和准确性：

##### 4.3.2.1 初筛Agent

| 功能模块 | 说明 |
| :--- | :--- |
| 简历结构化提取 | 从原始简历文本中提取标准化结构化信息 |
| 硬性条件过滤 | 检验学历、经验、技能、证书、地点、薪资等基本要求 |
| 语义匹配打分 | 基于NLP技术计算人岗语义相似度 |

| 硬性条件 | 过滤规则 |
| :--- | :--- |
| 学历要求 | 对比岗位要求与候选人最高学历 |
| 经验要求 | 检查工作年限是否满足 |
| 技能要求 | 验证必需技能是否具备 |
| 证书要求 | 检查相关资质证书 |
| 地点要求 | 匹配工作地点与候选人偏好 |
| 薪资要求 | 验证薪资期望是否在范围内 |

##### 4.3.2.2 深度评估Agent

基于冰山模型+STAR框架进行软素质评估：

| 冰山维度 | 权重 | 评估内容 |
| :--- | :--- | :--- |
| 知识 (Knowledge) | 0.15 | 专业背景、行业理解 |
| 技能 (Skills) | 0.20 | 硬技能、软技能匹配度 |
| 自我认知 (Self-knowledge) | 0.15 | 自我评价、成长潜力 |
| 特质 (Traits) | 0.20 | 性格特点、行为模式 |
| 动机 (Motives) | 0.15 | 求职动机、职业追求 |
| 价值观 (Values) | 0.15 | 价值取向、文化认同 |

##### 4.3.2.3 评价等级定义

| 等级 | 分数范围 | 决策建议 | 说明 |
| :--- | :--- | :--- | :--- |
| A | ≥85分 | 强烈推荐 | 综合评价优秀，建议进入下一轮 |
| B | 70-84分 | 推荐 | 综合评价良好，建议面试 |
| C | 55-69分 | 待定 | 综合评价一般，需进一步确认 |
| D | <55分 | 不推荐 | 综合评价不满足要求 |

##### 4.3.2.4 综合评分计算

```
最终得分 = 初筛得分 × 40% + 深度评估得分 × 60%

初筛得分 = 硬性条件通过分 × 40% + 语义匹配分 × 60%

深度评估得分 = 综合软素质分 × 50% + 文化匹配分 × 25% + 成长潜力分 × 25%
```

### 4.4 流程调度服务

#### 4.4.1 状态机设计

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

### 4.5 安全管控服务

#### 4.5.1 脱敏规则设计

| 数据类型 | 脱敏方式 | 示例 |
| :--- | :--- | :--- |
| 手机号 | 中间4位掩码 | 138****8888 |
| 邮箱 | @前1位后掩码 | a***@example.com |
| 姓名 | 姓+* | 张** |
| 身份证 | 前后各3位 | 110****1234 |

---

## 5. 数据库设计

### 5.1 数据库表结构

#### 5.1.1 企业表（companies）

| 字段名 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | VARCHAR(36) | PRIMARY KEY | 企业唯一标识 |
| name | VARCHAR(255) | NOT NULL | 企业名称 |
| mcp_server_url | VARCHAR(500) | NOT NULL | MCP Server 地址 |
| api_key | VARCHAR(255) | NOT NULL | API 密钥 |
| status | VARCHAR(20) | DEFAULT 'active' | 状态 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

#### 5.1.2 岗位表（jobs）

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
| status | VARCHAR(20) | DEFAULT 'open' | 状态 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

#### 5.1.3 匹配记录表（matches）

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

### 5.2 索引设计

| 表名 | 索引名 | 字段 | 类型 |
| :--- | :--- | :--- | :--- |
| jobs | idx_jobs_company_id | company_id | BTREE |
| jobs | idx_jobs_status | status | BTREE |
| jobs | idx_jobs_tags | tags | GIN |
| candidates | idx_candidates_skills | skills | GIN |
| matches | idx_matches_job_id | job_id | BTREE |
| matches | idx_matches_candidate_id | candidate_id | BTREE |
| matches | idx_matches_score | score | BTREE |
| enterprise_evaluations | idx_enterprise_company_id | company_id | BTREE |
| candidate_evaluations | idx_candidate_evaluations_candidate_id | candidate_id | BTREE |
| candidate_evaluations | idx_candidate_evaluations_job_id | job_id | BTREE |

### 5.3 评价模块数据库设计

#### 5.3.1 企业评价表（enterprise_evaluations）

| 字段名 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | VARCHAR(36) | PRIMARY KEY | 评价唯一标识 |
| company_id | VARCHAR(36) | NOT NULL, INDEX | 企业标识 |
| seven_s_data | JSONB | - | 7S模型评价数据 |
| seven_s_overall_score | DECIMAL(5,2) | DEFAULT 0 | 7S综合得分 |
| cash_flow_data | JSONB | - | 现金流分析数据 |
| cash_flow_score | DECIMAL(5,2) | DEFAULT 0 | 现金流评分 |
| dupont_data | JSONB | - | 杜邦分析数据 |
| dupont_score | DECIMAL(5,2) | DEFAULT 0 | 杜邦评分 |
| porter_data | JSONB | - | 波特五力数据 |
| porter_score | DECIMAL(5,2) | DEFAULT 0 | 波特五力评分 |
| overall_score | DECIMAL(5,2) | DEFAULT 0 | 综合竞争力得分 |
| competitiveness_level | VARCHAR(20) | - | 竞争力等级 |
| strengths | JSONB | - | 优势列表 |
| weaknesses | JSONB | - | 劣势列表 |
| opportunities | JSONB | - | 机会列表 |
| threats | JSONB | - | 威胁列表 |
| evaluation_date | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 评价日期 |
| valid_until | TIMESTAMP | - | 有效期 |

#### 5.3.2 候选人评价表（candidate_evaluations）

| 字段名 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | VARCHAR(36) | PRIMARY KEY | 评价唯一标识 |
| candidate_id | VARCHAR(36) | NOT NULL, INDEX | 候选人标识 |
| job_id | VARCHAR(36) | NOT NULL, INDEX | 岗位标识 |
| current_stage | VARCHAR(30) | DEFAULT 'initial_screening' | 当前阶段 |
| final_score | DECIMAL(5,2) | DEFAULT 0 | 最终综合得分 |
| percentile | DECIMAL(5,2) | DEFAULT 0 | 百分位排名 |
| evaluation_level | VARCHAR(10) | - | 评价等级(A/B/C/D) |
| recommendation | VARCHAR(20) | - | 建议(strong_buy/buy/hold/reject) |
| decision_reasons | JSONB | - | 决策原因 |
| evaluation_date | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 评价日期 |

#### 5.3.3 初筛结果表（initial_screenings）

| 字段名 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | VARCHAR(36) | PRIMARY KEY | 记录唯一标识 |
| evaluation_id | VARCHAR(36) | FOREIGN KEY | 评价标识 |
| candidate_id | VARCHAR(36) | NOT NULL | 候选人标识 |
| job_id | VARCHAR(36) | NOT NULL | 岗位标识 |
| structured_resume_data | JSONB | - | 结构化简历数据 |
| hard_condition_data | JSONB | - | 硬性条件过滤结果 |
| semantic_match_data | JSONB | - | 语义匹配结果 |
| screening_score | DECIMAL(5,2) | DEFAULT 0 | 初筛得分 |
| screening_passed | BOOLEAN | DEFAULT FALSE | 是否通过 |
| recommendations | JSONB | - | 建议列表 |
| concerns | JSONB | - | 关注点列表 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

#### 5.3.4 深度评估表（deep_assessments）

| 字段名 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | VARCHAR(36) | PRIMARY KEY | 记录唯一标识 |
| evaluation_id | VARCHAR(36) | FOREIGN KEY | 评价标识 |
| candidate_id | VARCHAR(36) | NOT NULL | 候选人标识 |
| job_id | VARCHAR(36) | NOT NULL | 岗位标识 |
| interview_questions_data | JSONB | - | 面试问题数据 |
| soft_quality_data | JSONB | - | 软素质评分数据 |
| overall_soft_score | DECIMAL(5,2) | DEFAULT 0 | 综合软素质得分 |
| culture_fit_score | DECIMAL(5,2) | DEFAULT 0 | 文化匹配度 |
| growth_potential_score | DECIMAL(5,2) | DEFAULT 0 | 成长潜力 |
| assessment_score | DECIMAL(5,2) | DEFAULT 0 | 综合评估得分 |
| key_strengths | JSONB | - | 关键优势 |
| development_areas | JSONB | - | 发展领域 |
| risk_indicators | JSONB | - | 风险指标 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

---

## 6. API 接口设计

### 6.1 匹配服务接口

| 接口路径 | HTTP 方法 | 功能描述 |
| :--- | :--- | :--- |
| `/api/v1/match/job/{job_id}` | POST | 岗位匹配候选人 |
| `/api/v1/match/candidate/{candidate_id}` | POST | 候选人匹配岗位 |
| `/api/v1/match/async/job/{job_id}` | POST | 异步岗位匹配 |
| `/api/v1/match/async/candidate/{candidate_id}` | POST | 异步候选人匹配 |
| `/api/v1/match/task/{task_id}` | GET | 查询任务状态 |

### 6.2 异步任务接口

| 接口路径 | HTTP 方法 | 功能描述 |
| :--- | :--- | :--- |
| `/api/v1/tasks/{task_id}` | GET | 获取任务状态 |
| `/api/v1/tasks/{task_id}/cancel` | POST | 取消任务 |
| `/api/v1/tasks` | GET | 获取任务列表 |

### 6.7 评价服务接口

#### 6.7.1 企业评价接口

| 接口路径 | HTTP 方法 | 功能描述 |
| :--- | :--- | :--- |
| `/api/v1/evaluations/enterprise` | POST | 创建企业评价 |
| `/api/v1/evaluations/enterprise/{company_id}` | GET | 获取企业评价历史 |
| `/api/v1/evaluations/enterprise/latest/{company_id}` | GET | 获取企业最新评价 |
| `/api/v1/evaluations/enterprise/report/{evaluation_id}` | GET | 获取企业评价报告 |

#### 6.7.2 候选人评价接口

| 接口路径 | HTTP 方法 | 功能描述 |
| :--- | :--- | :--- |
| `/api/v1/evaluations/candidate` | POST | 创建候选人评价 |
| `/api/v1/evaluations/candidate/{evaluation_id}` | GET | 获取候选人评价详情 |
| `/api/v1/evaluations/candidate/initial/{evaluation_id}` | GET | 获取初筛结果 |
| `/api/v1/evaluations/candidate/deep/{evaluation_id}` | GET | 获取深度评估结果 |
| `/api/v1/evaluations/candidate/job/{job_id}/evaluations` | GET | 获取岗位的所有评价 |
| `/api/v1/evaluations/candidate/report/{evaluation_id}` | GET | 获取候选人评价报告 |

---

## 7. 部署方案

### 7.1 Docker Compose 配置

```yaml
version: '3.8'

services:
  # API Gateway
  api-gateway:
    build: ./api-gateway
    ports:
      - "8000:8000"
    deploy:
      replicas: 3
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/jobagent
      - REDIS_URL=redis://redis-cluster:6379

  # 匹配引擎服务
  match-engine:
    build: ./match-engine
    deploy:
      replicas: 4
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/jobagent
      - REDIS_URL=redis://redis-cluster:6379

  # Celery Worker
  celery-worker:
    build: ./celery-worker
    deploy:
      replicas: 2
    environment:
      - CELERY_BROKER_URL=redis://redis-cluster:6379
      - CELERY_RESULT_BACKEND=redis://redis-cluster:6379

  # PostgreSQL 主库
  postgres-master:
    image: postgres:16
    volumes:
      - postgres_master_data:/var/lib/postgresql/data

  # PostgreSQL 从库
  postgres-slave:
    image: postgres:16
    volumes:
      - postgres_slave_data:/var/lib/postgresql/data

  # Redis Cluster
  redis-cluster:
    image: redis:7
    deploy:
      replicas: 6

volumes:
  postgres_master_data:
  postgres_slave_data:
```

### 7.2 Kubernetes 部署要点

| 资源类型 | 配置说明 |
| :--- | :--- |
| Deployment | 副本数 3-5，自动扩缩容 |
| Service | ClusterIP 类型，负载均衡 |
| Ingress | Nginx Ingress Controller |
| ConfigMap | 配置文件管理 |
| Secret | 敏感信息管理 |
| HorizontalPodAutoscaler | CPU/内存阈值自动扩缩容 |

---

## 8. 监控与告警

### 8.1 监控指标

| 指标类型 | 监控项 | 告警阈值 |
| :--- | :--- | :--- |
| 服务指标 | 请求响应时间 | > 3s |
| 服务指标 | 错误率 | > 5% |
| 服务指标 | QPS | > 1000 |
| 数据库指标 | 查询响应时间 | > 500ms |
| 数据库指标 | 连接数 | > 80% |
| 缓存指标 | 命中率 | < 90% |
| 任务队列 | 队列长度 | > 1000 |

### 8.2 日志结构

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

## 9. 代码安全性

### 9.1 安全风险矩阵

| 风险类型 | 风险描述 | 关联模块 | 解决方案 |
| :--- | :--- | :--- | :--- |
| 注入攻击 | SQL 注入、命令注入 | 数据库访问层 | ORM 参数化查询 |
| 数据泄露 | 敏感数据明文存储 | 数据存储层 | AES-256 加密 |
| 身份伪造 | 恶意 Agent 冒充 | 认证模块 | API Key + 签名验证 |
| 拒绝服务 | 大量请求导致服务不可用 | 网关层 | 限流熔断 |
| 协议漏洞 | MCP 协议实现缺陷 | MCP 网关 | 使用成熟 SDK |

---

## 10. 附录

### 10.1 版本历史

| 版本 | 日期 | 修改内容 | 作者 |
| :--- | :--- | :--- | :--- |
| v1.0 | 2026-06-12 | 初始版本 | Tech Team |
| v2.0 | 2026-06-12 | 添加高并发和分布式设计 | Tech Team |
| v2.1 | 2026-06-12 | 添加企业评价和候选人评价模块 | Tech Team |

### 10.2 参考文档

- 《Job Agent 系统 - 产品需求文档（PRD）》
- MCP 协议规范 v1.0
- FastAPI 官方文档
- Celery 官方文档
- PostgreSQL 主从复制指南
- Redis Cluster 部署指南

