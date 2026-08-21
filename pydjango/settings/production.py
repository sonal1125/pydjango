from .base import *


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False #as deploying

ALLOWED_HOSTS = [
    "pydjango-0g7h.onrender.com",
]

CSRF_TRUSTED_ORIGINS = [
    "https://pydjango-0g7h.onrender.com",
]

#render postgree database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME"),
        "USER": os.environ.get("DB_USER"),
        "PASSWORD": os.environ.get("DB_PASSWORD"),
        "HOST": os.environ.get("DB_HOST"),
        "PORT": os.environ.get("DB_PORT", "5432"),
        "OPTIONS": {
            "sslmode": "require",
            "channel_binding": "require",
        },
    }
}