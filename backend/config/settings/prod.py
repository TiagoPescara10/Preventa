"""Production settings (Render)."""

from .base import *  # noqa: F403

DEBUG = False

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Frontend (Vercel) and API (Render) live on different domains.
JWT_REFRESH_COOKIE["SECURE"] = True  # noqa: F405
JWT_REFRESH_COOKIE["SAMESITE"] = "None"  # noqa: F405
