"""Role-based DRF permissions. The backend is the source of truth for access."""

from rest_framework.permissions import BasePermission


class _TieneRol(BasePermission):
    rol: str = ""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, "rol", None) == self.rol)


class IsAdmin(_TieneRol):
    rol = "ADMIN"


class IsOperador(_TieneRol):
    rol = "OPERADOR"


class IsCliente(_TieneRol):
    rol = "CLIENTE"
