import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "student_budget_tracker.settings")

application = get_asgi_application()

