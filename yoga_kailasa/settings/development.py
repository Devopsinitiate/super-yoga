"""
Development settings — DEBUG on, LocMemCache, console email, relaxed security.
"""
from .base import *  # noqa: F401, F403

DEBUG = True

# WhiteNoise — plain storage in dev (no manifest hashing needed)
STATICFILES_STORAGE = 'whitenoise.storage.StaticFilesStorage'

# Email — print to console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Logging — verbose in dev
LOGGING['loggers']['yoga_app']['level'] = 'DEBUG'  # noqa: F405

# Cache — always LocMemCache in dev to avoid Redis connection issues
# (CACHES is already set to LocMemCache in base.py)
