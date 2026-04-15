"""
Production settings — DEBUG off, Redis cache, SMTP email, full security headers.
Set DJANGO_ENV=production in your environment to activate this file.
"""
import os
import socket
from .base import *  # noqa: F401, F403

DEBUG = False

# ── Static files ──────────────────────────────────────────────────────────────

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ── Email ─────────────────────────────────────────────────────────────────────

EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.smtp.EmailBackend'
)

# ── Cache — Redis if reachable, else LocMemCache ──────────────────────────────

_redis_url = os.environ.get('REDIS_URL', '')
if _redis_url:
    try:
        _host = _redis_url.split('//')[1].split(':')[0]
        _port = int(_redis_url.split(':')[-1].split('/')[0])
        _sock = socket.create_connection((_host, _port), timeout=1)
        _sock.close()
        CACHES = {  # noqa: F405
            'default': {
                'BACKEND': 'django.core.cache.backends.redis.RedisCache',
                'LOCATION': _redis_url,
                'TIMEOUT': 300,
            }
        }
    except (OSError, IndexError, ValueError):
        pass  # Stay on LocMemCache

# ── Security headers ──────────────────────────────────────────────────────────

SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True').lower() == 'true'
SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'True').lower() == 'true'
CSRF_COOKIE_SECURE = os.environ.get('CSRF_COOKIE_SECURE', 'True').lower() == 'true'
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
