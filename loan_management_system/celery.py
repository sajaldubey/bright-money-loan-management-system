import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "loan_management_system.settings")

app = Celery("loan_management_system")
app.config_from_object("django.conf:settings", namespace="Celery")
app.autodiscover_tasks()
