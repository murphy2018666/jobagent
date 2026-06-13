
# Job Agent 智能招聘匹配平台

> Job Agent 是一个基于 MCP（Model Context Protocol）协议的智能招聘匹配平台，连接企业与求职者，实现岗位与候选人的智能匹配。

## 📋 项目概述

Job Agent 平台提供以下核心能力：

- **MCP 协议网关**：标准化的 Agent 接入协议，支持企业和候选人 Agent 跨平台互联
- **智能匹配引擎**：基于语义分析的岗位-候选人匹配算法
- **流程管理**：完整的招聘流程追踪和状态管理
- **分布式架构**：支持高并发、高可用的分布式部署

## 🛠️ 技术栈

| 分类 | 技术 | 版本 |
| :--- | :--- | :--- |
| 语言 | Python | 3.11+ |
| 框架 | FastAPI | 0.100+ |
| 数据库 | PostgreSQL | 16+ |
| 缓存 | Redis | 7.0+ |
| 任务队列 | Celery | 5.3+ |
| 部署 | Docker / Kubernetes | - |

## 📁 项目结构

```
jobagent/
├── src/
│   └── jobagent/
│       ├── application/        # 应用层
│       │   ├── services/       # 应用服务
│       │   └── dto/            # 数据传输对象
│       ├── domain/             # 领域层
│       │   ├── entities/       # 领域实体
│       │   ├── repositories/   # 仓储接口
│       │   └── services/       # 领域服务
│       ├── infrastructure/     # 基础设施层
│       │   ├── database/       # 数据库实现
│       │   ├── cache/          # 缓存实现
│       │   ├── security/       # 安全组件
│       │   ├── mcp_protocol/   # MCP协议实现
│       │   ├── matching_engine/# 匹配引擎
│       │   ├── task_queue/     # 异步任务队列
│       │   ├── distributed/    # 分布式组件
│       │   ├── circuit_breaker/# 限流熔断
│       │   └── database_cluster/# 数据库集群
│       ├── interfaces/         # 接口层
│       │   ├── api/            # REST API
│       │   └── mcp_gateway/    # MCP网关
│       ├── config/             # 配置管理
│       └── main.py             # 应用入口
├── tests/                      # 测试代码
├── docs/                       # 文档
├── requirements.txt            # 依赖列表
├── .env                        # 环境变量
└── README.md                   # 项目说明
```

## 🚀 快速开始

### 环境要求

- Python 3.11+
- PostgreSQL 16+
- Redis 7.0+

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

复制 `.env` 文件并修改配置：

```bash
cp .env.example .env
```

配置项说明：

| 配置项 | 说明 | 默认值 |
| :--- | :--- | :--- |
| DATABASE_URL | 数据库连接地址 | postgresql://... |
| REDIS_URL | Redis连接地址 | redis://localhost:6379/0 |
| SECRET_KEY | JWT密钥 | - |
| RATE_LIMIT_ENABLED | 是否启用限流 | true |
| CIRCUIT_BREAKER_ENABLED | 是否启用熔断器 | true |

### 启动服务

```bash
# 启动 API 服务
python -m uvicorn src.jobagent.main:app --host 0.0.0.0 --port 8000 --reload

# 启动 Celery Worker
celery -A src.jobagent.infrastructure.task_queue.celery worker --loglevel=info

# 启动 Celery Beat（定时任务）
celery -A src.jobagent.infrastructure.task_queue.celery beat --loglevel=info
```

### 访问服务

- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

## 🐳 Docker 部署

### 使用 Docker Compose

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

### Docker 镜像构建

```bash
# 构建镜像
docker build -t jobagent:latest .

# 运行容器
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://admin:password@postgres:5432/jobagent \
  -e REDIS_URL=redis://redis:6379/0 \
  jobagent:latest
```

## ☸️ Kubernetes 部署

### 部署命令

```bash
# 使用部署脚本
./scripts/deploy.sh --kubernetes

# 或者手动部署
kubectl create namespace jobagent
kubectl apply -f kubernetes/secrets.yaml -n jobagent
kubectl apply -f kubernetes/statefulset.yaml -n jobagent
kubectl apply -f kubernetes/service.yaml -n jobagent
kubectl apply -f kubernetes/deployment.yaml -n jobagent
kubectl apply -f kubernetes/ingress.yaml -n jobagent
kubectl apply -f kubernetes/hpa.yaml -n jobagent
```

### 验证部署

```bash
# 查看 Pod 状态
kubectl get pods -n jobagent

# 查看服务
kubectl get services -n jobagent

# 查看 HPA
kubectl get hpa -n jobagent

# 查看日志
kubectl logs -f deployment/jobagent-api -n jobagent
```

### 清理部署

```bash
# 使用部署脚本
./scripts/deploy.sh --clean-kubernetes

# 或者手动清理
kubectl delete -f kubernetes/ -n jobagent
kubectl delete namespace jobagent
```

## 🏗️ 高并发与分布式设计

### 核心组件

#### 1. 分布式锁
基于 Redis 的分布式锁实现，支持自动续约和超时释放：

```python
from infrastructure.distributed import distributed_lock

with distributed_lock.acquire("job_update_lock"):
    # 执行需要互斥的操作
    update_job(job_id)
```

#### 2. 分布式 ID 生成器
采用类似 Snowflake 的方案，生成全局唯一 ID：

```python
from infrastructure.distributed import id_generator

job_id = id_generator.generate()
```

#### 3. 限流组件
基于 Redis 计数器的限流实现：

```python
from infrastructure.distributed import rate_limiter

if rate_limiter.is_allowed(client_ip, max_requests=100, window_seconds=60):
    # 处理请求
```

#### 4. 熔断器
保护服务免受级联故障影响：

```python
from infrastructure.circuit_breaker import circuit_breaker

@circuit_breaker.decorate("external_api")
def call_external_service():
    # 调用外部服务
```

#### 5. 数据库读写分离
自动路由读操作到从库：

```python
from infrastructure.database_cluster import transaction_manager

# 读操作（自动路由到从库）
result = await transaction_manager.execute_read(query_func)

# 写操作（路由到主库）
result = await transaction_manager.execute_write(query_func)
```

### 性能优化策略

| 策略 | 说明 | 实现方式 |
| :--- | :--- | :--- |
| 异步任务 | 耗时操作异步化 | Celery 任务队列 |
| 缓存策略 | 多级缓存架构 | 本地缓存 + Redis |
| 读写分离 | 数据库负载均衡 | PostgreSQL 主从复制 |
| 水平扩展 | 服务集群化 | Docker/Kubernetes |
| 限流熔断 | 保护系统稳定 | Redis 计数器 + 熔断器模式 |

## 🔌 API 接口

### 健康检查

```http
GET /health
```

### 匹配服务

```http
# 同步匹配
POST /api/v1/match/job/{job_id}

# 异步匹配
POST /api/v1/match/async/job/{job_id}

# 查询任务状态
GET /api/v1/tasks/{task_id}
```

### 企业服务

```http
POST /api/v1/companies
GET /api/v1/companies/{company_id}
PUT /api/v1/companies/{company_id}
DELETE /api/v1/companies/{company_id}
```

### 岗位服务

```http
POST /api/v1/jobs
GET /api/v1/jobs
GET /api/v1/jobs/{job_id}
PUT /api/v1/jobs/{job_id}
DELETE /api/v1/jobs/{job_id}
```

### 候选人服务

```http
POST /api/v1/candidates
GET /api/v1/candidates/{candidate_id}
PUT /api/v1/candidates/{candidate_id}
DELETE /api/v1/candidates/{candidate_id}
```

### MCP 协议端点

```http
POST /mcp/v1/invoke
POST /mcp/v1/register
POST /mcp/v1/list_operations
```

## 🧪 测试

```bash
# 运行单元测试
pytest tests/

# 运行集成测试
pytest tests/integration/

# 生成测试报告
pytest --cov=src --cov-report=html
```

## 📖 文档

- **产品需求文档**: `docs/JOB_AGENT_SYSTEM_PRD.md`
- **技术设计文档**: `docs/JOB_AGENT_SYSTEM_TDD_V2.md`

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

*本项目基于 MCP 协议构建，实现企业与求职者的智能匹配*
