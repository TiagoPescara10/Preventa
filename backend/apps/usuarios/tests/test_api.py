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

    assert user.get_username() == "admin@example.com"
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
@pytest.mark.parametrize("escrito", ["ANA@EXAMPLE.COM", "Ana@Example.com", "  ana@example.com "])
def test_login_no_distingue_mayusculas_en_el_email(api, escrito):
    # Bug #105
    UsuarioFactory(email="ana@example.com")

    response = login(api, escrito)

    assert response.status_code == 200
    assert response.data["usuario"]["email"] == "ana@example.com"


@pytest.mark.django_db
def test_login_funciona_si_el_usuario_se_creo_con_mayusculas(api):
    # Bug #105
    Usuario.objects.create_user(email="Beto@Example.com", password=PASSWORD, nombre="Beto")

    assert login(api, "beto@example.com").status_code == 200
    assert login(api, "BETO@EXAMPLE.COM").status_code == 200


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


# --- gestión de usuarios (/api/v1/usuarios/) ----------------------------------

PASSWORD_FUERTE = "Distribuidora-Cordoba-2026"


@pytest.fixture
def admin():
    return UsuarioFactory(rol=Rol.ADMIN, email="admin@example.com")


@pytest.fixture
def api_admin(api, admin):
    api.force_authenticate(admin)
    return api


def url_usuario(usuario, accion=None):
    if accion:
        return reverse(f"usuario-{accion}", args=[usuario.pk])
    return reverse("usuario-detail", args=[usuario.pk])


def assert_sin_password(data):
    """No key named password (or a hash) anywhere in the payload."""
    texto = str(data).lower()
    assert "password" not in texto
    assert "md5$" not in texto  # test hasher prefix


@pytest.mark.django_db
@pytest.mark.parametrize("rol", [Rol.OPERADOR, Rol.CLIENTE])
@pytest.mark.parametrize(
    ("metodo", "accion"),
    [
        ("get", "list"),
        ("post", "list"),
        ("get", "detail"),
        ("patch", "detail"),
        ("post", "desactivar"),
        ("post", "activar"),
    ],
)
def test_usuarios_solo_admin_otros_roles_reciben_403(api, rol, metodo, accion):
    otro = UsuarioFactory()
    api.force_authenticate(UsuarioFactory(rol=rol))
    url = (
        reverse("usuario-list")
        if accion == "list"
        else reverse(f"usuario-{accion}", args=[otro.pk])
    )

    response = getattr(api, metodo)(url, {}, format="json")

    assert response.status_code == 403


@pytest.mark.django_db
def test_usuarios_sin_token_devuelve_401(api):
    assert api.get(reverse("usuario-list")).status_code == 401


@pytest.mark.django_db
def test_usuarios_no_tiene_delete_ni_put(api_admin):
    otro = UsuarioFactory()

    assert api_admin.delete(url_usuario(otro)).status_code == 405
    assert api_admin.put(url_usuario(otro), {}, format="json").status_code == 405
    otro.refresh_from_db()
    assert otro.is_active


# --- listar -------------------------------------------------------------------


@pytest.mark.django_db
def test_listar_usuarios_paginado(api_admin, admin):
    UsuarioFactory.create_batch(3)

    response = api_admin.get(reverse("usuario-list"))

    assert response.status_code == 200
    assert response.data["count"] == 4
    assert {"id", "email", "nombre", "rol", "activo"} <= set(response.data["results"][0])
    assert_sin_password(response.data)


@pytest.mark.django_db
def test_listar_usuarios_page_size(api_admin):
    UsuarioFactory.create_batch(3)

    response = api_admin.get(reverse("usuario-list"), {"page_size": 2})

    assert len(response.data["results"]) == 2
    assert response.data["next"]


@pytest.mark.django_db
def test_listar_usuarios_busca_por_email_o_nombre(api_admin):
    por_nombre = UsuarioFactory(nombre="Marta Gómez")
    por_email = UsuarioFactory(email="marta.ventas@example.com", nombre="Otra")
    UsuarioFactory(nombre="Juan")

    response = api_admin.get(reverse("usuario-list"), {"search": "marta"})

    assert {u["id"] for u in response.data["results"]} == {por_nombre.pk, por_email.pk}


@pytest.mark.django_db
def test_listar_usuarios_filtra_por_rol_y_activo(api_admin):
    operador = UsuarioFactory(rol=Rol.OPERADOR)
    UsuarioFactory(rol=Rol.OPERADOR, is_active=False)
    UsuarioFactory(rol=Rol.CLIENTE)

    response = api_admin.get(reverse("usuario-list"), {"rol": "OPERADOR", "activo": "true"})

    assert [u["id"] for u in response.data["results"]] == [operador.pk]


@pytest.mark.django_db
def test_listar_usuarios_filtro_inactivos(api_admin):
    inactivo = UsuarioFactory(is_active=False)

    response = api_admin.get(reverse("usuario-list"), {"activo": "false"})

    assert [u["id"] for u in response.data["results"]] == [inactivo.pk]


@pytest.mark.django_db
def test_listar_usuarios_filtro_invalido_devuelve_400(api_admin):
    assert api_admin.get(reverse("usuario-list"), {"rol": "JEFE"}).status_code == 400


# --- crear --------------------------------------------------------------------


@pytest.mark.django_db
def test_crear_usuario(api_admin):
    body = {
        "email": "nuevo@example.com",
        "nombre": "Nuevo Operador",
        "rol": "OPERADOR",
        "password": PASSWORD_FUERTE,
    }

    response = api_admin.post(reverse("usuario-list"), body, format="json")

    assert response.status_code == 201
    assert response.data["email"] == "nuevo@example.com"
    assert response.data["rol"] == "OPERADOR"
    assert response.data["activo"] is True
    assert_sin_password(response.data)
    creado = Usuario.objects.get(email="nuevo@example.com")
    assert creado.check_password(PASSWORD_FUERTE)


@pytest.mark.django_db
def test_usuario_creado_puede_loguearse(api_admin):
    api_admin.post(
        reverse("usuario-list"),
        {"email": "n@example.com", "nombre": "N", "rol": "CLIENTE", "password": PASSWORD_FUERTE},
        format="json",
    )

    assert login(APIClient(), "n@example.com", PASSWORD_FUERTE).status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize(
    "password",
    [
        "corta1",  # too short
        "12345678901",  # only numbers
        "password123",  # common
        "marta.gomez.ventas",  # too similar to the email
    ],
)
def test_crear_usuario_con_password_debil_devuelve_400(api_admin, password):
    body = {
        "email": "marta.gomez.ventas@example.com",
        "nombre": "Marta Gómez",
        "rol": "OPERADOR",
        "password": password,
    }

    response = api_admin.post(reverse("usuario-list"), body, format="json")

    assert response.status_code == 400
    assert "password" in response.data
    assert not Usuario.objects.filter(email=body["email"]).exists()


@pytest.mark.django_db
def test_crear_usuario_con_email_repetido_devuelve_400(api_admin, admin):
    body = {"email": admin.email, "nombre": "X", "rol": "OPERADOR", "password": PASSWORD_FUERTE}

    response = api_admin.post(reverse("usuario-list"), body, format="json")

    assert response.status_code == 400
    assert "email" in response.data


@pytest.mark.django_db
def test_crear_usuario_con_email_que_solo_difiere_en_mayusculas_devuelve_400(api_admin):
    # Bug #105
    UsuarioFactory(email="ana@example.com")
    body = {
        "email": "Ana@Example.com",
        "nombre": "Ana",
        "rol": "OPERADOR",
        "password": PASSWORD_FUERTE,
    }

    response = api_admin.post(reverse("usuario-list"), body, format="json")

    assert response.status_code == 400
    assert response.data["email"] == ["Ya existe un usuario con este email."]
    assert Usuario.objects.filter(email__iexact="ana@example.com").count() == 1


@pytest.mark.django_db
def test_crear_usuario_guarda_el_email_en_minusculas(api_admin):
    # Bug #105
    body = {
        "email": "  Nuevo.Operador@Example.com ",
        "nombre": "Nuevo",
        "rol": "OPERADOR",
        "password": PASSWORD_FUERTE,
    }

    response = api_admin.post(reverse("usuario-list"), body, format="json")

    assert response.status_code == 201
    assert response.data["email"] == "nuevo.operador@example.com"
    assert Usuario.objects.filter(email="nuevo.operador@example.com").exists()


@pytest.mark.django_db
def test_crear_usuario_campos_obligatorios(api_admin):
    response = api_admin.post(reverse("usuario-list"), {}, format="json")

    assert response.status_code == 400
    assert {"email", "nombre", "rol", "password"} <= set(response.data)


# --- detalle ------------------------------------------------------------------


@pytest.mark.django_db
def test_detalle_usuario(api_admin):
    usuario = UsuarioFactory(rol=Rol.CLIENTE)

    response = api_admin.get(url_usuario(usuario))

    assert response.status_code == 200
    assert response.data["id"] == usuario.pk
    assert response.data["email"] == usuario.email
    assert_sin_password(response.data)


@pytest.mark.django_db
def test_detalle_usuario_inexistente_devuelve_404(api_admin):
    assert api_admin.get(reverse("usuario-detail", args=[999999])).status_code == 404


# --- editar -------------------------------------------------------------------


@pytest.mark.django_db
def test_editar_nombre_y_rol(api_admin):
    usuario = UsuarioFactory(rol=Rol.CLIENTE)

    response = api_admin.patch(
        url_usuario(usuario), {"nombre": "Nombre Nuevo", "rol": "OPERADOR"}, format="json"
    )

    assert response.status_code == 200
    assert response.data["nombre"] == "Nombre Nuevo"
    assert response.data["rol"] == "OPERADOR"
    assert_sin_password(response.data)


@pytest.mark.django_db
def test_editar_no_cambia_email_ni_password(api_admin):
    usuario = UsuarioFactory()
    email = usuario.email

    response = api_admin.patch(
        url_usuario(usuario),
        {"email": "otro@example.com", "password": PASSWORD_FUERTE, "nombre": "Ok"},
        format="json",
    )

    assert response.status_code == 200
    usuario.refresh_from_db()
    assert usuario.email == email
    assert usuario.check_password(PASSWORD)
    assert usuario.nombre == "Ok"


@pytest.mark.django_db
def test_editar_rol_invalido_devuelve_400(api_admin):
    usuario = UsuarioFactory()

    assert api_admin.patch(url_usuario(usuario), {"rol": "JEFE"}, format="json").status_code == 400


@pytest.mark.django_db
def test_rn15_admin_no_puede_quitarse_el_rol_admin_devuelve_409(api_admin, admin):
    response = api_admin.patch(url_usuario(admin), {"rol": "OPERADOR"}, format="json")

    assert response.status_code == 409
    assert response.data["codigo"] == "RN-15"
    admin.refresh_from_db()
    assert admin.rol == Rol.ADMIN


@pytest.mark.django_db
def test_rn15_admin_puede_quitarle_el_rol_admin_a_otro_admin(api_admin):
    otro = UsuarioFactory(rol=Rol.ADMIN)

    response = api_admin.patch(url_usuario(otro), {"rol": "OPERADOR"}, format="json")

    assert response.status_code == 200
    assert response.data["rol"] == "OPERADOR"
    otro.refresh_from_db()
    assert otro.rol == Rol.OPERADOR


# --- activar / desactivar -----------------------------------------------------


@pytest.mark.django_db
def test_desactivar_usuario(api_admin):
    usuario = UsuarioFactory()

    response = api_admin.post(url_usuario(usuario, "desactivar"))

    assert response.status_code == 200
    assert response.data["activo"] is False
    assert_sin_password(response.data)
    assert Usuario.objects.filter(pk=usuario.pk, is_active=False).exists()


@pytest.mark.django_db
def test_rn15_admin_no_puede_desactivarse_a_si_mismo_devuelve_409(api_admin, admin):
    response = api_admin.post(url_usuario(admin, "desactivar"))

    assert response.status_code == 409
    assert response.data["codigo"] == "RN-15"
    admin.refresh_from_db()
    assert admin.is_active


@pytest.mark.django_db
def test_rn15_admin_puede_desactivar_a_otro_admin(api_admin):
    otro = UsuarioFactory(rol=Rol.ADMIN)

    response = api_admin.post(url_usuario(otro, "desactivar"))

    assert response.status_code == 200
    assert response.data["activo"] is False
    otro.refresh_from_db()
    assert not otro.is_active


@pytest.mark.django_db
def test_activar_usuario(api_admin):
    usuario = UsuarioFactory(is_active=False)

    response = api_admin.post(url_usuario(usuario, "activar"))

    assert response.status_code == 200
    assert response.data["activo"] is True


@pytest.mark.django_db
def test_usuario_desactivado_pierde_acceso(api_admin):
    usuario = UsuarioFactory()
    cliente = APIClient()
    access = login(cliente, usuario.email).data["access"]

    api_admin.post(url_usuario(usuario, "desactivar"))

    # Cannot log in, refresh (the cookie from the earlier login) or use the access token.
    assert login(APIClient(), usuario.email).status_code == 401
    assert cliente.post(reverse("auth-refresh")).status_code == 401
    cliente.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    assert cliente.get(reverse("auth-me")).status_code == 401
