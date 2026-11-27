"""User management routes, mounted at /api/v1/usuarios/ (auth routes live in urls.py)."""

from rest_framework.routers import SimpleRouter

from .views import UsuarioViewSet

router = SimpleRouter()
router.register("", UsuarioViewSet, basename="usuario")

urlpatterns = router.urls
