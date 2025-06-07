# Gunicorn配置文件

import multiprocessing

# 绑定地址和端口
bind = "0.0.0.0:5003"

# 工作进程数（建议设置为CPU核心数的2-4倍）
workers = multiprocessing.cpu_count() * 2 + 1

# 工作模式
worker_class = "sync"

# 每个工作进程的线程数
threads = 2

# 超时时间（秒）
timeout = 300

# 保持连接时间
keepalive = 5

# 最大请求数（防止内存泄漏）
max_requests = 1000
max_requests_jitter = 50

# 日志配置
accesslog = "-"
errorlog = "-"
loglevel = "info"

# 进程名称
proc_name = 'plate_recognition'

# 预加载应用
preload_app = True

# 优雅重启
graceful_timeout = 30