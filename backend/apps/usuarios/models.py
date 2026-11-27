"""Usuario: custom user model, login by email, one role per user."""

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower

from core.models import TimeStampedModel


class Rol(models.TextChoices):
    ADMIN = "ADMIN", "Administrador"
    OPERADOR = "OPERADOR", "Operador"
    CLIENTE = "CLIENTE", "Cliente"


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    @classmethod
    def normalize_email(cls, email):
        """Emails are case-insensitive: lowercase the whole address and strip spaces.

        Django's default only lowercases the domain (#105).
        """
        return (email or "").strip().lower()

    def get_by_natural_key(self, username):
        # Used by authenticate(): lets the login work whatever the case typed.
        return self.get(**{self.model.USERNAME_FIELD: self.normalize_email(username)})

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

    - Login with email (no username). The email is stored lowercase and is unique
      ignoring case, also in the database (#105).
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
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                name="usuario_email_unico_sin_mayusculas",
                violation_error_message="Ya existe un usuario con este email.",
            ),
        ]

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        # Covers every write path (admin, factories, plain .save()), not only the manager.
        self.email = self.__class__.objects.normalize_email(self.email)
        super().save(*args, **kwargs)

    @property
    def activo(self) -> bool:
        return self.is_active
