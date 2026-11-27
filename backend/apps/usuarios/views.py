"""Auth endpoints and user management (ADMIN only).

The access token goes in the response body (the frontend keeps it in memory).
The refresh token is only ever sent as an httpOnly cookie.
"""

from contextlib import suppress

from django.conf import settings
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from core.permissions import IsAdmin

from . import selectors, services
from .serializers import (
    UsuarioAdminSerializer,
    UsuarioCrearSerializer,
    UsuarioEditarSerializer,
    UsuarioFiltroSerializer,
    UsuarioSerializer,
)

COOKIE = settings.JWT_REFRESH_COOKIE


def _set_refresh_cookie(response, refresh: str):
    response.set_cookie(
        COOKIE["NAME"],
        refresh,
        max_age=COOKIE["MAX_AGE"],
        path=COOKIE["PATH"],
        httponly=COOKIE["HTTPONLY"],
        secure=COOKIE["SECURE"],
        samesite=COOKIE["SAMESITE"],
    )


class LoginView(TokenObtainPairView):
    """POST email + password -> {"access": ...} and refresh cookie."""

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0]) from e

        data = serializer.validated_data
        response = Response(
            {"access": data["access"], "usuario": UsuarioSerializer(serializer.user).data},
            status=status.HTTP_200_OK,
        )
        _set_refresh_cookie(response, data["refresh"])
        return response


class RefreshView(APIView):
    """POST with the refresh cookie -> new {"access": ...}."""

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        request=None,
        responses=inline_serializer("AccessToken", {"access": serializers.CharField()}),
    )
    def post(self, request):
        refresh = request.COOKIES.get(COOKIE["NAME"])
        if not refresh:
            return Response(
                {"detail": "Falta el refresh token."}, status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = TokenRefreshSerializer(data={"refresh": refresh})
        try:
            serializer.is_valid(raise_exception=True)
        except (TokenError, AuthenticationFailed):
            # Covers InvalidToken and a deactivated user. Returned directly: with
            # no authentication_classes DRF would turn AuthenticationFailed into a 403.
            return Response(
                {"detail": "Refresh token inválido o expirado."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        response = Response({"access": serializer.validated_data["access"]})
        if "refresh" in serializer.validated_data:  # only when ROTATE_REFRESH_TOKENS is on
            _set_refresh_cookie(response, serializer.validated_data["refresh"])
        return response


class LogoutView(APIView):
    """POST -> blacklists the refresh token and deletes its cookie."""

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        refresh = request.COOKIES.get(COOKIE["NAME"])
        if refresh:
            # Already invalid or expired: nothing to revoke.
            with suppress(TokenError):
                RefreshToken(refresh).blacklist()

        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie(COOKIE["NAME"], path=COOKIE["PATH"], samesite=COOKIE["SAMESITE"])
        return response


class MeView(APIView):
    """GET the authenticated user."""

    @extend_schema(responses=UsuarioSerializer)
    def get(self, request):
        return Response(UsuarioSerializer(request.user).data)


@extend_schema_view(
    list=extend_schema(parameters=[UsuarioFiltroSerializer]),
    create=extend_schema(request=UsuarioCrearSerializer, responses={201: UsuarioAdminSerializer}),
    partial_update=extend_schema(request=UsuarioEditarSerializer),
    desactivar=extend_schema(request=None),
    activar=extend_schema(request=None),
)
class UsuarioViewSet(viewsets.GenericViewSet):
    """User management: list, create, detail, edit nombre/rol, activar/desactivar.

    No DELETE: users are deactivated (RN-09). Only ADMIN.
    """

    permission_classes = [IsAdmin]
    serializer_class = UsuarioAdminSerializer
    queryset = selectors.listar_usuarios()
    http_method_names = ["get", "post", "patch", "head", "options"]

    def list(self, request):
        filtros = UsuarioFiltroSerializer(data=request.query_params.dict())
        filtros.is_valid(raise_exception=True)
        f = filtros.validated_data
        usuarios = selectors.listar_usuarios(
            busqueda=f.get("search"), rol=f.get("rol"), activo=f.get("activo")
        )
        page = self.paginate_queryset(usuarios)
        return self.get_paginated_response(UsuarioAdminSerializer(page, many=True).data)

    def create(self, request):
        entrada = UsuarioCrearSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        usuario = services.crear_usuario(**entrada.validated_data)
        return Response(UsuarioAdminSerializer(usuario).data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        return Response(UsuarioAdminSerializer(self._get_usuario(pk)).data)

    def partial_update(self, request, pk=None):
        usuario = self._get_usuario(pk)
        entrada = UsuarioEditarSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        usuario = services.editar_usuario(
            usuario=usuario, actor=request.user, **entrada.validated_data
        )
        return Response(UsuarioAdminSerializer(usuario).data)

    @action(detail=True, methods=["post"])
    def desactivar(self, request, pk=None):
        usuario = services.desactivar_usuario(usuario=self._get_usuario(pk), actor=request.user)
        return Response(UsuarioAdminSerializer(usuario).data)

    @action(detail=True, methods=["post"])
    def activar(self, request, pk=None):
        usuario = services.activar_usuario(usuario=self._get_usuario(pk))
        return Response(UsuarioAdminSerializer(usuario).data)

    def _get_usuario(self, pk):
        return get_object_or_404(selectors.listar_usuarios(), pk=pk)
