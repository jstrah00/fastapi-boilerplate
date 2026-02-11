"""Gunicorn configuration for A2W production deployment."""

bind = "0.0.0.0:8000"
workers = 3
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
keepalive = 5
accesslog = "-"
errorlog = "-"
loglevel = "info"
