import multiprocessing

# Server socket
bind = "127.0.0.1:8000"

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"

# Timeouts
timeout = 120
keepalive = 5

# Process management
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "/var/log/eduorbit/gunicorn.log"
errorlog = "/var/log/eduorbit/gunicorn.log"
loglevel = "info"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
