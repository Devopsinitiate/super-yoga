"""
Gunicorn configuration for Yoga Kailasa.
Golden ratio applied to worker count: workers ≈ (2 × CPU cores) + 1
"""
import multiprocessing
import os

# ─── Server socket ────────────────────────────────────────────────────────────
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
backlog = 2048

# ─── Workers ──────────────────────────────────────────────────────────────────
# Golden ratio: φ ≈ 1.618 — worker count scales naturally with CPU
workers = int(os.environ.get('WEB_CONCURRENCY', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2

# ─── Logging ──────────────────────────────────────────────────────────────────
accesslog = '-'   # stdout
errorlog = '-'    # stderr
loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sµs'

# ─── Process naming ───────────────────────────────────────────────────────────
proc_name = 'yoga_kailasa'

# ─── Security ─────────────────────────────────────────────────────────────────
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# ─── Graceful restart ─────────────────────────────────────────────────────────
graceful_timeout = 30
max_requests = 1000
max_requests_jitter = 50
