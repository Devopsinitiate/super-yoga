# Settings package — imports from the appropriate module based on DJANGO_ENV.
# Default: development. Set DJANGO_ENV=production in production environments.
import os

env = os.environ.get('DJANGO_ENV', 'development')

if env == 'production':
    from .production import *  # noqa: F401, F403
else:
    from .development import *  # noqa: F401, F403
