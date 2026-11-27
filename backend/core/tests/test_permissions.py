"""Unit tests of the role permissions in core.permissions (no database, no HTTP)."""

import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory

from apps.usuarios.models import Rol
from apps.usuarios.tests.factories import UsuarioFactory
from core.permissions import IsAdmin, IsCliente, IsOperador

PERMISOS = [(IsAdmin, Rol.ADMIN), (IsOperador, Rol.OPERADOR), (IsCliente, Rol.CLIENTE)]


def tiene_permiso(permiso, user):
    request = APIRequestFactory().get("/")
    request.user = user
    return permiso().has_permission(request, view=None)


@pytest.mark.parametrize(("permiso", "rol_permitido"), PERMISOS)
@pytest.mark.parametrize("rol", list(Rol))
def test_cada_permiso_solo_deja_pasar_a_su_rol(permiso, rol_permitido, rol):
    user = UsuarioFactory.build(rol=rol)

    assert tiene_permiso(permiso, user) is (rol == rol_permitido)


@pytest.mark.parametrize(("permiso", "_rol"), PERMISOS)
def test_usuario_anonimo_no_tiene_permiso(permiso, _rol):
    assert tiene_permiso(permiso, AnonymousUser()) is False


@pytest.mark.parametrize(("permiso", "rol"), PERMISOS)
def test_usuario_inactivo_no_tiene_permiso_aunque_tenga_el_rol(permiso, rol):
    user = UsuarioFactory.build(rol=rol, is_active=False)

    assert tiene_permiso(permiso, user) is False


@pytest.mark.parametrize(("permiso", "rol"), PERMISOS)
def test_usuario_inactivo_de_otro_rol_no_tiene_permiso(permiso, rol):
    otro_rol = next(r for r in Rol if r != rol)
    user = UsuarioFactory.build(rol=otro_rol, is_active=False)

    assert tiene_permiso(permiso, user) is False
