"""Auth endpoints.

The access token goes in the response body (the frontend keeps it in memory).
The refresh token is only ever sent as an httpOnly cookie.
"""

from contextlib import suppress

from django.conf import settings
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import UsuarioSerializer

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
        except (TokenError, InvalidToken):
            # Returned directly: with no authentication_classes DRF would turn
            # an AuthenticationFailed into a 403.
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
