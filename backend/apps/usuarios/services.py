"""Business rules for usuarios (user and role management).

Rules raise core.exceptions.ReglaDeNegocioError. Input format (including password
strength) is validated by the serializers before reaching these functions.
"""

from django.db import transaction

from core.exceptions import ConflictoError

from .models import Rol, Usuario

# RN-15: an admin cannot deactivate themselves or drop their own ADMIN role.
CODIGO_PROTECCION_ADMIN = "RN-15"


def _preparar_vinculo_cliente(usuario: Usuario) -> None:
    """Hook for the rol CLIENTE -> Cliente link.

    TODO(HU-05): when the Cliente model exists (Sprint 2), a usuario with
    rol CLIENTE must have a cliente: require it here and reject (400) otherwise.
    """


@transaction.atomic
def crear_usuario(*, email: str, nombre: str, rol: str, password: str) -> Usuario:
    usuario = Usuario.objects.create_user(email=email, password=password, nombre=nombre, rol=rol)
    _preparar_vinculo_cliente(usuario)
    return usuario


@transaction.atomic
def editar_usuario(
    *, usuario: Usuario, actor: Usuario, nombre: str | None = None, rol: str | None = None
) -> Usuario:
    """Edit nombre and/or rol. The email is not editable.

    An admin cannot drop their own ADMIN role (RN-15).
    """
    if rol is not None and usuario.pk == actor.pk and usuario.rol == Rol.ADMIN and rol != Rol.ADMIN:
        raise ConflictoError(CODIGO_PROTECCION_ADMIN, "No podés quitarte el rol de Administrador.")

    campos = []
    if nombre is not None:
        usuario.nombre = nombre
        campos.append("nombre")
    if rol is not None:
        usuario.rol = rol
        campos.append("rol")
    if campos:
        usuario.save(update_fields=[*campos, "actualizado_en"])
        _preparar_vinculo_cliente(usuario)
    return usuario


@transaction.atomic
def desactivar_usuario(*, usuario: Usuario, actor: Usuario) -> Usuario:
    """Baja logica (RN-09). Idempotent. The user can no longer log in or refresh.

    An admin cannot deactivate themselves (RN-15).
    """
    if usuario.pk == actor.pk:
        raise ConflictoError(CODIGO_PROTECCION_ADMIN, "No podés desactivar tu propio usuario.")
    if usuario.is_active:
        usuario.is_active = False
        usuario.save(update_fields=["is_active", "actualizado_en"])
    return usuario


@transaction.atomic
def activar_usuario(*, usuario: Usuario) -> Usuario:
    """Undo the baja logica. Idempotent."""
    if not usuario.is_active:
        usuario.is_active = True
        usuario.save(update_fields=["is_active", "actualizado_en"])
    return usuario
