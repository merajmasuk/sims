from .base import *  # noqa

DEBUG = True

# In local dev, relax host/CORS checks
ALLOWED_HOSTS = ["*"]
CORS_ALLOW_ALL_ORIGINS = True

# Quieter axes in dev
AXES_ENABLED = False
