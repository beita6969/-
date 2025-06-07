#!/bin/bash

echo "🚀 智能车牌识别系统部署脚本"
echo "================================"

# 检查参数
if [ "$1" == "" ]; then
    echo "使用方法: ./deploy.sh [选项]"
    echo "选项:"
    echo "  local    - 本地Docker部署"
    echo "  server   - 服务器部署"
    echo "  build    - 只构建镜像"
    echo "  stop     - 停止服务"
    echo "  logs     - 查看日志"
    exit 1
fi

# 本地部署
if [ "$1" == "local" ]; then
    echo "📦 开始本地Docker部署..."
    
    # 构建镜像
    echo "🔨 构建Docker镜像..."
    docker-compose build
    
    # 启动服务
    echo "🚀 启动服务..."
    docker-compose up -d
    
    echo "✅ 部署完成！"
    echo "访问地址: http://localhost"
    echo "查看日志: docker-compose logs -f"
fi

# 服务器部署
if [ "$1" == "server" ]; then
    echo "🌐 服务器部署准备..."
    
    # 创建部署包
    echo "📦 创建部署包..."
    tar -czf plate_recognition_deploy.tar.gz \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='test_*' \
        --exclude='uploads/*' \
        --exclude='results/*' \
        --exclude='.git' \
        --exclude='venv' \
        --exclude='env' \
        .
    
    echo "✅ 部署包创建完成: plate_recognition_deploy.tar.gz"
    echo ""
    echo "📋 服务器部署步骤:"
    echo "1. 上传部署包到服务器"
    echo "   scp plate_recognition_deploy.tar.gz user@server:/path/to/deploy/"
    echo ""
    echo "2. 在服务器上解压"
    echo "   tar -xzf plate_recognition_deploy.tar.gz"
    echo ""
    echo "3. 安装Docker和Docker Compose"
    echo "   curl -fsSL https://get.docker.com | sh"
    echo "   sudo usermod -aG docker $USER"
    echo ""
    echo "4. 修改nginx配置中的域名"
    echo "   编辑 nginx/nginx.conf，将 your_domain.com 替换为实际域名"
    echo ""
    echo "5. 启动服务"
    echo "   docker-compose up -d"
fi

# 只构建镜像
if [ "$1" == "build" ]; then
    echo "🔨 构建Docker镜像..."
    docker-compose build
    echo "✅ 镜像构建完成！"
fi

# 停止服务
if [ "$1" == "stop" ]; then
    echo "🛑 停止服务..."
    docker-compose down
    echo "✅ 服务已停止！"
fi

# 查看日志
if [ "$1" == "logs" ]; then
    docker-compose logs -f
fi