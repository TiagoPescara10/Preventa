"""Local development settings."""

from .base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Local dev runs over http, so the refresh cookie cannot be Secure.
JWT_REFRESH_COOKIE["SECURE"] = False  # noqa: F405
