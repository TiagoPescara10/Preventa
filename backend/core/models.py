"""Abstract base models shared by every app."""

from django.db import models


class TimeStampedModel(models.Model):
    """Adds creado_en / actualizado_en to every table."""

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteQuerySet(models.QuerySet):
    def activos(self):
        return self.filter(activo=True)

    def inactivos(self):
        return self.filter(activo=False)


class SoftDeleteModel(TimeStampedModel):
    """Baja logica: records are deactivated, never physically deleted (RN-09)."""

    activo = models.BooleanField(default=True)

    objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        abstract = True

    def desactivar(self):
        self.activo = False
        self.save(update_fields=["activo", "actualizado_en"])

    def activar(self):
        self.activo = True
        self.save(update_fields=["activo", "actualizado_en"])
