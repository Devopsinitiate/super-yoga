# Settings package - imports from the appropriate module based on DJANGO_ENV.
# Default: development. Set DJANGO_ENV=production in production environments.
import os

from django.core.exceptions import ImproperlyConfigured

env = os.environ.get('DJANGO_ENV', 'development').strip().lower()

if env == 'production':
    from .production import *  # noqa: F401, F403
elif env == 'development':
    from .development import *  # noqa: F401, F403
else:
    raise ImproperlyConfigured(
        f"Invalid DJANGO_ENV value: {env!r}. "
        "Expected 'development' or 'production'."
    )
