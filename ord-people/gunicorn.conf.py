import os

workers = int(os.getenv("GUNICORN_WORKERS", "3"))
worker_class = "uvicorn.workers.UvicornWorker"
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")

loglevel = "info"
accesslog = "-"
errorlog = "-"

timeout = 30
keepalive = 5
graceful_timeout = 30

forwarded_allow_ips = os.getenv("FORWARDED_ALLOW_IPS", "127.0.0.1")
proxy_protocol = False
proxy_allow_ips = os.getenv("FORWARDED_ALLOW_IPS", "127.0.0.1")
