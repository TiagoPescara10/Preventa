"""Root URL configuration: every API route lives under /api/v1/."""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from core.views import health

api_v1 = [
    path("health/", health, name="health"),
    path("auth/", include("apps.usuarios.urls")),
    path("usuarios/", include("apps.usuarios.urls_gestion")),
    path("clientes/", include("apps.clientes.urls")),
    path("catalogo/", include("apps.catalogo.urls")),
    path("pedidos/", include("apps.pedidos.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_v1)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
