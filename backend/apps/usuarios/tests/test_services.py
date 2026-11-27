"""Business rule tests for usuarios services."""

import pytest

from apps.usuarios import selectors, services
from apps.usuarios.models import Rol
from core.exceptions import ConflictoError

from .factories import UsuarioFactory

pytestmark = pytest.mark.django_db


# --- crear --------------------------------------------------------------------


def test_crear_usuario_guarda_el_password_hasheado():
    usuario = services.crear_usuario(
        email="ana@Example.com", nombre="Ana", rol=Rol.OPERADOR, password="una-clave-larga-42"
    )

    assert usuario.email == "ana@example.com"
    assert usuario.rol == Rol.OPERADOR
    assert usuario.is_active
    assert usuario.password != "una-clave-larga-42"
    assert usuario.check_password("una-clave-larga-42")


def test_crear_usuario_cliente_sin_vinculo_por_ahora():
    # TODO(HU-05): should fail without a cliente once the link exists.
    usuario = services.crear_usuario(
        email="almacen@example.com", nombre="Almacén", rol=Rol.CLIENTE, password="clave-larga-42"
    )

    assert usuario.rol == Rol.CLIENTE


# --- editar -------------------------------------------------------------------


def test_editar_cambia_nombre_y_rol():
    admin = UsuarioFactory(rol=Rol.ADMIN)
    usuario = UsuarioFactory(rol=Rol.CLIENTE)

    services.editar_usuario(usuario=usuario, actor=admin, nombre="Nuevo", rol=Rol.OPERADOR)

    usuario.refresh_from_db()
    assert usuario.nombre == "Nuevo"
    assert usuario.rol == Rol.OPERADOR


def test_rn15_admin_no_puede_quitarse_el_rol_admin():
    admin = UsuarioFactory(rol=Rol.ADMIN)

    with pytest.raises(ConflictoError) as exc:
        services.editar_usuario(usuario=admin, actor=admin, rol=Rol.OPERADOR)

    assert exc.value.codigo == "RN-15"
    admin.refresh_from_db()
    assert admin.rol == Rol.ADMIN


def test_rn15_admin_puede_editar_su_nombre_y_mantener_rol_admin():
    admin = UsuarioFactory(rol=Rol.ADMIN)

    services.editar_usuario(usuario=admin, actor=admin, nombre="Yo", rol=Rol.ADMIN)

    admin.refresh_from_db()
    assert admin.nombre == "Yo"
    assert admin.rol == Rol.ADMIN


def test_rn15_admin_puede_quitar_el_rol_admin_a_otro_admin():
    admin = UsuarioFactory(rol=Rol.ADMIN)
    otro = UsuarioFactory(rol=Rol.ADMIN)

    services.editar_usuario(usuario=otro, actor=admin, rol=Rol.OPERADOR)

    otro.refresh_from_db()
    assert otro.rol == Rol.OPERADOR


# --- activar / desactivar (RN-09) ---------------------------------------------


def test_rn09_desactivar_es_baja_logica():
    admin = UsuarioFactory(rol=Rol.ADMIN)
    usuario = UsuarioFactory()

    services.desactivar_usuario(usuario=usuario, actor=admin)

    usuario.refresh_from_db()
    assert not usuario.is_active  # still in the table, only deactivated


def test_rn15_admin_no_puede_desactivarse_a_si_mismo():
    admin = UsuarioFactory(rol=Rol.ADMIN)

    with pytest.raises(ConflictoError) as exc:
        services.desactivar_usuario(usuario=admin, actor=admin)

    assert exc.value.codigo == "RN-15"
    admin.refresh_from_db()
    assert admin.is_active


def test_rn15_admin_puede_desactivar_a_otro_admin():
    admin = UsuarioFactory(rol=Rol.ADMIN)
    otro = UsuarioFactory(rol=Rol.ADMIN)

    services.desactivar_usuario(usuario=otro, actor=admin)

    otro.refresh_from_db()
    assert not otro.is_active


def test_rn09_activar_reactiva_un_usuario():
    usuario = UsuarioFactory(is_active=False)

    services.activar_usuario(usuario=usuario)

    usuario.refresh_from_db()
    assert usuario.is_active


def test_activar_y_desactivar_son_idempotentes():
    admin = UsuarioFactory(rol=Rol.ADMIN)
    usuario = UsuarioFactory()

    services.activar_usuario(usuario=usuario)
    services.desactivar_usuario(usuario=usuario, actor=admin)
    services.desactivar_usuario(usuario=usuario, actor=admin)

    usuario.refresh_from_db()
    assert not usuario.is_active


# --- selectors ----------------------------------------------------------------


def test_listar_usuarios_filtra_por_busqueda_rol_y_activo():
    ana = UsuarioFactory(email="ana@example.com", nombre="Ana Pérez", rol=Rol.OPERADOR)
    UsuarioFactory(email="beto@example.com", nombre="Beto", rol=Rol.CLIENTE)
    inactiva = UsuarioFactory(email="carla@example.com", nombre="Carla Ana", is_active=False)

    assert set(selectors.listar_usuarios(busqueda="ANA")) == {ana, inactiva}
    assert list(selectors.listar_usuarios(busqueda="ana@")) == [ana]
    assert list(selectors.listar_usuarios(rol=Rol.OPERADOR)) == [ana]
    assert list(selectors.listar_usuarios(activo=False)) == [inactiva]
    assert list(selectors.listar_usuarios(busqueda="ana", activo=True)) == [ana]
