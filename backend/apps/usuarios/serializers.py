"""Usuario serializers: input validation and output shape.

No serializer here ever outputs the password: it is write_only on input.
"""

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Rol, Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    """Shape used by the auth endpoints (login, /me)."""

    class Meta:
        model = Usuario
        fields = ["id", "email", "nombre", "rol"]
        read_only_fields = fields


class UsuarioAdminSerializer(serializers.ModelSerializer):
    """Output of the user management endpoints."""

    activo = serializers.BooleanField(source="is_active", read_only=True)

    class Meta:
        model = Usuario
        fields = ["id", "email", "nombre", "rol", "activo", "creado_en", "actualizado_en"]
        read_only_fields = fields


class UsuarioCrearSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = Usuario
        fields = ["email", "nombre", "rol", "password"]
        extra_kwargs = {"rol": {"required": True}}

    def validate(self, attrs):
        # Unsaved instance so UserAttributeSimilarityValidator can compare
        # the password against email and nombre.
        candidato = Usuario(email=attrs["email"], nombre=attrs["nombre"], rol=attrs["rol"])
        try:
            validate_password(attrs["password"], user=candidato)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)}) from e
        return attrs


class UsuarioEditarSerializer(serializers.Serializer):
    """PATCH body. Only nombre and rol; any other field (email, password...) is ignored."""

    nombre = serializers.CharField(max_length=150, required=False)
    rol = serializers.ChoiceField(choices=Rol.choices, required=False)


class UsuarioFiltroSerializer(serializers.Serializer):
    """Query params of the list endpoint."""

    search = serializers.CharField(required=False, help_text="Busca en email o nombre")
    rol = serializers.ChoiceField(choices=Rol.choices, required=False)
    activo = serializers.BooleanField(required=False, allow_null=True, default=None)
