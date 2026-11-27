"""Usuario serializers: input validation and output shape."""

from rest_framework import serializers

from .models import Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ["id", "email", "nombre", "rol"]
        read_only_fields = fields
