
#!/bin/bash

set -e

echo "=== Job Agent Deployment Script ==="

# 检查命令是否存在
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo "Error: $1 is not installed. Please install it first."
        exit 1
    fi
}

# Docker Compose 部署
deploy_docker() {
    echo "Deploying with Docker Compose..."
    
    check_command docker
    check_command docker-compose
    
    # 构建镜像
    echo "Building Docker image..."
    docker-compose build
    
    # 启动服务
    echo "Starting services..."
    docker-compose up -d
    
    echo "Docker deployment completed successfully!"
    echo "Services running:"
    docker-compose ps
}

# Kubernetes 部署
deploy_kubernetes() {
    echo "Deploying to Kubernetes..."
    
    check_command kubectl
    
    # 创建命名空间
    echo "Creating namespace..."
    kubectl create namespace jobagent || true
    
    # 创建 secrets
    echo "Creating secrets..."
    kubectl apply -f kubernetes/secrets.yaml -n jobagent
    
    # 创建 StatefulSets
    echo "Creating StatefulSets..."
    kubectl apply -f kubernetes/statefulset.yaml -n jobagent
    
    # 等待数据库就绪
    echo "Waiting for database to be ready..."
    kubectl wait --for=condition=ready pod/postgres-0 -n jobagent --timeout=5m
    
    # 创建 Services
    echo "Creating services..."
    kubectl apply -f kubernetes/service.yaml -n jobagent
    
    # 创建 Deployments
    echo "Creating deployments..."
    kubectl apply -f kubernetes/deployment.yaml -n jobagent
    
    # 创建 Ingress
    echo "Creating ingress..."
    kubectl apply -f kubernetes/ingress.yaml -n jobagent
    
    # 创建 HPA
    echo "Creating HPA..."
    kubectl apply -f kubernetes/hpa.yaml -n jobagent
    
    echo "Kubernetes deployment completed successfully!"
    echo "Pods status:"
    kubectl get pods -n jobagent
}

# 清理 Docker Compose
clean_docker() {
    echo "Cleaning Docker Compose deployment..."
    docker-compose down -v
    echo "Docker cleanup completed!"
}

# 清理 Kubernetes
clean_kubernetes() {
    echo "Cleaning Kubernetes deployment..."
    kubectl delete -f kubernetes/ -n jobagent
    kubectl delete namespace jobagent
    echo "Kubernetes cleanup completed!"
}

# 显示帮助
show_help() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -d, --docker      Deploy with Docker Compose"
    echo "  -k, --kubernetes  Deploy to Kubernetes"
    echo "  -cd, --clean-docker      Clean Docker Compose deployment"
    echo "  -ck, --clean-kubernetes  Clean Kubernetes deployment"
    echo "  -h, --help        Show this help message"
}

# 解析参数
case "$1" in
    -d|--docker)
        deploy_docker
        ;;
    -k|--kubernetes)
        deploy_kubernetes
        ;;
    -cd|--clean-docker)
        clean_docker
        ;;
    -ck|--clean-kubernetes)
        clean_kubernetes
        ;;
    -h|--help)
        show_help
        ;;
    *)
        show_help
        exit 1
        ;;
esac
