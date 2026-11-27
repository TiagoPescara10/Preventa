"""Lowercase and strip existing emails before adding the case-insensitive unique constraint (#105)."""

from django.db import migrations
from django.db.models import Count
from django.db.models.functions import Lower, Trim


def normalizar_emails(apps, schema_editor):
    Usuario = apps.get_model("usuarios", "Usuario")

    # Two users whose emails only differ in case cannot be merged automatically:
    # stop with a clear message so someone decides which account to keep.
    repetidos = list(
        Usuario.objects.annotate(normalizado=Lower(Trim("email")))
        .values("normalizado")
        .annotate(n=Count("id"))
        .filter(n__gt=1)
        .values_list("normalizado", flat=True)
    )
    if repetidos:
        raise RuntimeError(
            "Hay usuarios con emails que solo difieren en mayúsculas o espacios: "
            f"{', '.join(sorted(repetidos))}. Resolvelos a mano antes de migrar."
        )

    Usuario.objects.update(email=Lower(Trim("email")))


class Migration(migrations.Migration):
    dependencies = [
        ("usuarios", "0001_initial"),
    ]

    operations = [
        # Reverse is a no-op: the original casing is not kept.
        migrations.RunPython(normalizar_emails, migrations.RunPython.noop),
    ]
