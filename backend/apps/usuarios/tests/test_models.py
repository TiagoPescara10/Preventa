"""Usuario model and database constraints."""

import pytest
from django.db import IntegrityError, connection, transaction

from apps.usuarios.models import Usuario

from .factories import UsuarioFactory

pytestmark = pytest.mark.django_db


# --- email sin distinguir mayúsculas (#105) ------------------------------------


def test_create_user_normaliza_el_email_a_minusculas_y_sin_espacios():
    user = Usuario.objects.create_user(email="  Ana.Perez@Example.COM ", password="x", nombre="Ana")

    assert user.email == "ana.perez@example.com"


def test_save_normaliza_el_email_aunque_no_pase_por_el_manager():
    user = UsuarioFactory()
    user.email = " Otro@Example.com"
    user.save()

    user.refresh_from_db()
    assert user.email == "otro@example.com"


def test_get_by_natural_key_no_distingue_mayusculas():
    user = UsuarioFactory(email="ana@example.com")

    assert Usuario.objects.get_by_natural_key(" ANA@Example.com ") == user


def test_la_base_rechaza_emails_que_solo_difieren_en_mayusculas():
    UsuarioFactory(email="ana@example.com")

    # Raw SQL skips the model's normalization: the constraint itself must reject it.
    with pytest.raises(IntegrityError), transaction.atomic(), connection.cursor() as cursor:
        cursor.execute(
            f"""
            INSERT INTO {Usuario._meta.db_table}
                (password, is_superuser, is_staff, is_active, date_joined,
                 creado_en, actualizado_en, email, nombre, rol)
            VALUES ('x', false, false, true, now(), now(), now(),
                    'ANA@example.com', 'Ana', 'CLIENTE')
            """
        )
