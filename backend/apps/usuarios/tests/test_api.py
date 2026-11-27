import pytest
from django.conf import settings
from django.urls import reverse
from rest_framework.test import APIClient

from apps.usuarios.models import Rol, Usuario

from .factories import UsuarioFactory

COOKIE = settings.JWT_REFRESH_COOKIE["NAME"]


@pytest.fixture
def api():
    return APIClient()


@pytest.mark.django_db
def test_crear_usuario_usa_email_como_login():
    user = Usuario.objects.create_user(email="Admin@Example.com", password="x", nombre="Ana")

    assert user.get_username() == "Admin@example.com"
    assert user.rol == Rol.CLIENTE


@pytest.mark.django_db
def test_login_devuelve_access_en_body_y_refresh_en_cookie_httponly(api):
    user = UsuarioFactory(rol=Rol.OPERADOR)

    response = api.post(
        reverse("auth-login"),
        {"email": user.email, "password": "clave-de-prueba-123"},
        format="json",
    )

    assert response.status_code == 200
    assert "access" in response.data
    assert "refresh" not in response.data
    assert response.data["usuario"]["rol"] == "OPERADOR"
    assert response.cookies[COOKIE]["httponly"]


@pytest.mark.django_db
def test_refresh_con_cookie_devuelve_nuevo_access(api):
    user = UsuarioFactory()
    api.post(
        reverse("auth-login"),
        {"email": user.email, "password": "clave-de-prueba-123"},
        format="json",
    )

    response = api.post(reverse("auth-refresh"))

    assert response.status_code == 200
    assert "access" in response.data


@pytest.mark.django_db
def test_refresh_sin_cookie_devuelve_401(api):
    assert api.post(reverse("auth-refresh")).status_code == 401


@pytest.mark.django_db
def test_me_requiere_autenticacion(api):
    assert api.get(reverse("auth-me")).status_code == 401
