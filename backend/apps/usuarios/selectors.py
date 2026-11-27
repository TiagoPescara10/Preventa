"""Reusable read queries for usuarios (filters by role, active users, ...)."""

from django.db.models import Q, QuerySet

from .models import Usuario


def listar_usuarios(
    *, busqueda: str | None = None, rol: str | None = None, activo: bool | None = None
) -> QuerySet[Usuario]:
    """Users ordered by email. `busqueda` matches email or nombre (case-insensitive)."""
    usuarios = Usuario.objects.all()
    if busqueda:
        usuarios = usuarios.filter(Q(email__icontains=busqueda) | Q(nombre__icontains=busqueda))
    if rol:
        usuarios = usuarios.filter(rol=rol)
    if activo is not None:
        usuarios = usuarios.filter(is_active=activo)
    return usuarios
