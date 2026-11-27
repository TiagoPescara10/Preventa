"""Permission matrix: every protected endpoint x every role, per the spec table
("Roles y permisos" in docs/especificacion.md).

To cover a new endpoint, add one Fila to MATRIZ. The guard test at the end fails
if an /api/v1/ route is neither in MATRIZ nor in PUBLICAS, so nothing is forgotten.

Requests go through the real JWT authentication (Bearer access token), not
force_authenticate, so the check is the same one the frontend hits.
"""

from collections.abc import Callable
from dataclasses import dataclass, field

import pytest
from django.urls import URLPattern, URLResolver, get_resolver, reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.usuarios.models import Rol
from apps.usuarios.tests.factories import UsuarioFactory

ANONIMO = "ANONIMO"
ROLES = [Rol.ADMIN, Rol.OPERADOR, Rol.CLIENTE, ANONIMO]


def esperado(admin, operador, cliente, anonimo=401):
    return {Rol.ADMIN: admin, Rol.OPERADOR: operador, Rol.CLIENTE: cliente, ANONIMO: anonimo}


# Shortcuts for the usual rows of the spec table.
def solo_admin(ok=200):
    return esperado(ok, 403, 403)


def todos_autenticados(ok=200):
    return esperado(ok, ok, ok)


@dataclass
class Contexto:
    """Objects the rows can point at. Add fields here as new apps appear."""

    otro_usuario: object


@dataclass
class Fila:
    accion: str  # wording close to the spec table, used as test id
    metodo: str
    ruta: str  # URL name
    codigos: dict
    args: Callable[[Contexto], list] = lambda ctx: []
    body: Callable[[Contexto], dict] = field(default=lambda ctx: {})


def _otro(ctx):
    return [ctx.otro_usuario.pk]


MATRIZ = [
    # --- auth ---
    Fila("ver mi usuario (/me)", "get", "auth-me", todos_autenticados()),
    # --- Gestionar usuarios y roles: solo Administrador ---
    Fila("listar usuarios", "get", "usuario-list", solo_admin()),
    Fila(
        "crear usuario",
        "post",
        "usuario-list",
        solo_admin(201),
        body=lambda ctx: {
            "email": "nuevo@example.com",
            "nombre": "Nuevo",
            "rol": Rol.OPERADOR,
            "password": "Distribuidora-Cordoba-2026",
        },
    ),
    Fila("ver usuario", "get", "usuario-detail", solo_admin(), args=_otro),
    Fila(
        "editar usuario",
        "patch",
        "usuario-detail",
        solo_admin(),
        args=_otro,
        body=lambda ctx: {"nombre": "Editado"},
    ),
    Fila("desactivar usuario", "post", "usuario-desactivar", solo_admin(), args=_otro),
    Fila("activar usuario", "post", "usuario-activar", solo_admin(), args=_otro),
]

# Routes that do not require authentication on purpose.
PUBLICAS = {"health", "auth-login", "auth-refresh", "auth-logout"}


CASOS = [
    pytest.param(fila, rol, id=f"{fila.accion}-{rol}".replace(" ", "_"))
    for fila in MATRIZ
    for rol in ROLES
]


@pytest.mark.django_db
@pytest.mark.parametrize(("fila", "rol"), CASOS)
def test_matriz_de_permisos(fila, rol):
    ctx = Contexto(otro_usuario=UsuarioFactory(rol=Rol.OPERADOR))
    api = APIClient()
    if rol != ANONIMO:
        user = UsuarioFactory(rol=rol)
        api.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")

    url = reverse(fila.ruta, args=fila.args(ctx))
    response = getattr(api, fila.metodo)(url, fila.body(ctx), format="json")

    assert response.status_code == fila.codigos[rol], response.data


# --- guards -------------------------------------------------------------------


def _nombres_de_rutas_api(patrones=None, prefijo=""):
    """URL names of every route under /api/v1/."""
    patrones = get_resolver().url_patterns if patrones is None else patrones
    nombres = set()
    for p in patrones:
        ruta = prefijo + str(p.pattern)
        if isinstance(p, URLResolver):
            nombres |= _nombres_de_rutas_api(p.url_patterns, ruta)
        elif isinstance(p, URLPattern) and ruta.startswith("api/v1/") and p.name:
            nombres.add(p.name)
    return nombres


def test_toda_ruta_de_la_api_esta_en_la_matriz_o_es_publica():
    cubiertas = {f.ruta for f in MATRIZ} | PUBLICAS

    sin_cubrir = _nombres_de_rutas_api() - cubiertas

    assert not sin_cubrir, f"Agregá estas rutas a MATRIZ (o a PUBLICAS): {sorted(sin_cubrir)}"


def test_cada_fila_define_los_cuatro_roles():
    for fila in MATRIZ:
        assert set(fila.codigos) == set(ROLES), fila.accion
