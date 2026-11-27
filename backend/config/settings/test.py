"""Settings used by pytest (locally and in CI)."""

from .base import *  # noqa: F403

DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost"]

# Fast hashing: tests create many users.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

JWT_REFRESH_COOKIE["SECURE"] = False  # noqa: F405
