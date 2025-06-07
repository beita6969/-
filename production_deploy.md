# 智能车牌识别系统生产环境部署指南

## 部署方案选择

### 方案一：Docker容器化部署（推荐）

#### 优势
- 环境一致性
- 易于扩展
- 简化部署流程
- 隔离性好

#### 系统要求
- Ubuntu 20.04/22.04 或 CentOS 7/8
- Docker 20.10+
- Docker Compose 1.29+
- 最低4GB RAM，推荐8GB+
- 50GB磁盘空间

### 方案二：传统部署（Nginx + Gunicorn）

#### 优势
- 更细粒度的控制
- 资源占用较少
- 适合单机部署

## Docker部署步骤

### 1. 服务器准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

### 2. 上传项目文件

```bash
# 在本地打包
chmod +x deploy.sh
./deploy.sh server

# 上传到服务器
scp plate_recognition_deploy.tar.gz user@your-server:/opt/

# 在服务器解压
ssh user@your-server
cd /opt
tar -xzf plate_recognition_deploy.tar.gz
cd plate_recognition
```

### 3. 配置修改

#### 修改nginx配置
```bash
vim nginx/nginx.conf
# 将 your_domain.com 替换为实际域名
```

#### 配置SSL证书（可选）
```bash
mkdir -p nginx/ssl
# 将SSL证书文件放入 nginx/ssl 目录
# cert.pem 和 key.pem
```

### 4. 启动服务

```bash
# 构建并启动
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 5. 配置防火墙

```bash
# 开放端口
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## 传统部署步骤

### 1. 安装系统依赖

```bash
# Python和系统包
sudo apt update
sudo apt install python3.9 python3.9-venv python3.9-dev
sudo apt install nginx supervisor
sudo apt install libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1
```

### 2. 创建虚拟环境

```bash
cd /opt/plate_recognition
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements_easyocr.txt
pip install gunicorn
```

### 3. 配置Gunicorn

```bash
# 测试Gunicorn
gunicorn --bind 0.0.0.0:5003 app_advanced:app

# 配置systemd服务
sudo cp systemd/plate_recognition.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable plate_recognition
sudo systemctl start plate_recognition
```

### 4. 配置Nginx

```bash
# 创建Nginx配置
sudo vim /etc/nginx/sites-available/plate_recognition

server {
    listen 80;
    server_name your_domain.com;
    
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://127.0.0.1:5003;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    location /static {
        alias /opt/plate_recognition/static;
        expires 30d;
    }
}

# 启用站点
sudo ln -s /etc/nginx/sites-available/plate_recognition /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 性能优化

### 1. Gunicorn优化
- 工作进程数：CPU核心数 * 2 + 1
- 使用gevent或eventlet处理并发
- 设置合理的超时时间

### 2. Nginx优化
- 启用Gzip压缩
- 配置静态文件缓存
- 使用HTTP/2

### 3. 系统优化
- 调整文件描述符限制
- 优化内核参数
- 使用SSD存储

## 监控和维护

### 1. 日志管理
```bash
# Docker日志
docker-compose logs -f plate-recognition

# 系统日志
journalctl -u plate_recognition -f
```

### 2. 性能监控
- 使用Prometheus + Grafana
- 监控CPU、内存、磁盘使用
- 设置告警规则

### 3. 备份策略
```bash
# 备份数据库
docker exec plate_recognition_app sqlite3 plate_records.db ".backup /backup/plate_records_$(date +%Y%m%d).db"

# 备份上传文件
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz uploads/
```

## 安全建议

1. **使用HTTPS**
   - 申请SSL证书（Let's Encrypt）
   - 强制HTTPS重定向

2. **访问控制**
   - 配置防火墙规则
   - 使用fail2ban防止暴力破解
   - 限制上传文件类型和大小

3. **定期更新**
   - 及时更新系统补丁
   - 更新Docker镜像
   - 监控安全公告

## 故障排查

### 常见问题

1. **端口被占用**
```bash
sudo lsof -i :5003
sudo kill -9 <PID>
```

2. **权限问题**
```bash
sudo chown -R www-data:www-data /opt/plate_recognition
sudo chmod -R 755 /opt/plate_recognition
```

3. **内存不足**
- 增加swap空间
- 减少Gunicorn工作进程数
- 优化模型加载

## 扩展部署

### 使用Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: plate-recognition
spec:
  replicas: 3
  selector:
    matchLabels:
      app: plate-recognition
  template:
    metadata:
      labels:
        app: plate-recognition
    spec:
      containers:
      - name: app
        image: plate-recognition:latest
        ports:
        - containerPort: 5003
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
```

### 使用云服务
- AWS EC2 + RDS
- Google Cloud Run
- Azure Container Instances
- 阿里云ECS + OSS

## 联系支持

如遇到部署问题，请提供以下信息：
- 操作系统版本
- Docker版本
- 错误日志
- 系统资源使用情况