import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'yoga_kailasa.settings')
app = Celery('yoga_kailasa')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
