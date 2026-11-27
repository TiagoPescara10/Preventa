"""Usuario: custom user model, login by email, one role per user."""

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models

from core.models import TimeStampedModel


class Rol(models.TextChoices):
    ADMIN = "ADMIN", "Administrador"
    OPERADOR = "OPERADOR", "Operador"
    CLIENTE = "CLIENTE", "Cliente"


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("rol", Rol.ADMIN)
        if not extra_fields["is_staff"] or not extra_fields["is_superuser"]:
            raise ValueError("Un superusuario necesita is_staff=True e is_superuser=True")
        return self._create_user(email, password, **extra_fields)


class Usuario(AbstractUser, TimeStampedModel):
    """A user of the platform.

    - Login with email (no username).
    - `is_active` from AbstractUser is the "activo" flag (baja logica, RN-09).
    - The link to Cliente (required when rol == CLIENTE) is added in a later sprint.
    """

    username = None
    first_name = None
    last_name = None

    email = models.EmailField("email", unique=True)
    nombre = models.CharField(max_length=150)
    rol = models.CharField(max_length=10, choices=Rol.choices, default=Rol.CLIENTE)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nombre"]

    objects = UsuarioManager()

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        ordering = ["email"]

    def __str__(self):
        return self.email

    @property
    def activo(self) -> bool:
        return self.is_active
