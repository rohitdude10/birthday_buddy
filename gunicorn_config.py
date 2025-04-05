import multiprocessing
import os

# Gunicorn configuration file for production deployment

# Server socket
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:5000")

# Worker processes
# Recommended: (2 x $num_cores) + 1
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"
threads = int(os.getenv("GUNICORN_THREADS", 2))

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")

# Process naming
proc_name = "birthday_buddy"

# SSL (uncomment if using SSL directly in Gunicorn)
# certfile = "/path/to/cert.pem"
# keyfile = "/path/to/key.pem"

# Timeout
timeout = int(os.getenv("GUNICORN_TIMEOUT", 30))

# Server mechanics
preload_app = True

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190 