import pytest
from django.conf import settings
from django.urls import reverse
from rest_framework.test import APIClient

from apps.usuarios.models import Rol, Usuario

from .factories import UsuarioFactory

COOKIE = settings.JWT_REFRESH_COOKIE["NAME"]
PASSWORD = "clave-de-prueba-123"


@pytest.fixture
def api():
    return APIClient()


def login(api, email, password=PASSWORD):
    return api.post(reverse("auth-login"), {"email": email, "password": password}, format="json")


# --- modelo -------------------------------------------------------------------


@pytest.mark.django_db
def test_crear_usuario_usa_email_como_login():
    user = Usuario.objects.create_user(email="Admin@Example.com", password="x", nombre="Ana")

    assert user.get_username() == "Admin@example.com"
    assert user.rol == Rol.CLIENTE


# --- login --------------------------------------------------------------------


@pytest.mark.django_db
def test_login_devuelve_access_en_body_y_refresh_en_cookie_httponly(api):
    user = UsuarioFactory(rol=Rol.OPERADOR)

    response = login(api, user.email)

    assert response.status_code == 200
    assert response.data["access"]
    assert "refresh" not in response.data
    assert response.data["usuario"]["rol"] == "OPERADOR"
    cookie = response.cookies[COOKIE]
    assert cookie.value
    assert cookie["httponly"]
    assert cookie["path"] == settings.JWT_REFRESH_COOKIE["PATH"]


@pytest.mark.django_db
def test_login_con_password_incorrecta_devuelve_401_sin_cookie(api):
    user = UsuarioFactory()

    response = login(api, user.email, password="otra-clave")

    assert response.status_code == 401
    assert response.data["detail"]
    assert "access" not in response.data
    assert COOKIE not in response.cookies


@pytest.mark.django_db
def test_login_con_email_inexistente_devuelve_el_mismo_mensaje(api):
    user = UsuarioFactory()

    password_mal = login(api, user.email, password="otra-clave")
    email_inexistente = login(api, "nadie@example.com")

    assert email_inexistente.status_code == 401
    assert email_inexistente.data == password_mal.data


@pytest.mark.django_db
def test_login_de_usuario_inactivo_devuelve_401(api):
    user = UsuarioFactory(is_active=False)

    response = login(api, user.email)

    assert response.status_code == 401
    assert COOKIE not in response.cookies


# --- refresh ------------------------------------------------------------------


@pytest.mark.django_db
def test_refresh_con_cookie_devuelve_nuevo_access(api):
    user = UsuarioFactory()
    access_login = login(api, user.email).data["access"]

    response = api.post(reverse("auth-refresh"))

    assert response.status_code == 200
    assert response.data["access"]
    assert response.data["access"] != access_login


@pytest.mark.django_db
def test_refresh_sin_cookie_devuelve_401(api):
    assert api.post(reverse("auth-refresh")).status_code == 401


@pytest.mark.django_db
def test_refresh_con_cookie_invalida_devuelve_401(api):
    api.cookies[COOKIE] = "no-es-un-jwt"

    assert api.post(reverse("auth-refresh")).status_code == 401


# --- logout -------------------------------------------------------------------


@pytest.mark.django_db
def test_logout_borra_la_cookie(api):
    user = UsuarioFactory()
    login(api, user.email)

    response = api.post(reverse("auth-logout"))

    assert response.status_code == 204
    cookie = response.cookies[COOKIE]
    assert cookie.value == ""
    assert cookie["max-age"] == 0
    assert cookie["path"] == settings.JWT_REFRESH_COOKIE["PATH"]


@pytest.mark.django_db
def test_logout_invalida_el_refresh(api):
    user = UsuarioFactory()
    refresh = login(api, user.email).cookies[COOKIE].value

    api.post(reverse("auth-logout"))
    # Reusing the old token (e.g. a stolen copy) must fail even though the
    # browser already dropped the cookie.
    api.cookies[COOKIE] = refresh
    response = api.post(reverse("auth-refresh"))

    assert response.status_code == 401


@pytest.mark.django_db
def test_logout_sin_cookie_devuelve_204(api):
    assert api.post(reverse("auth-logout")).status_code == 204


# --- me -----------------------------------------------------------------------


@pytest.mark.django_db
def test_me_con_token_devuelve_email_nombre_y_rol(api):
    user = UsuarioFactory(rol=Rol.ADMIN)
    access = login(api, user.email).data["access"]
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    response = api.get(reverse("auth-me"))

    assert response.status_code == 200
    assert response.data["email"] == user.email
    assert response.data["nombre"] == user.nombre
    assert response.data["rol"] == "ADMIN"


@pytest.mark.django_db
def test_me_requiere_autenticacion(api):
    assert api.get(reverse("auth-me")).status_code == 401
