import factory

from apps.usuarios.models import Rol, Usuario


class UsuarioFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Usuario
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"usuario{n}@example.com")
    nombre = factory.Faker("name", locale="es_AR")
    rol = Rol.CLIENTE
    password = factory.PostGenerationMethodCall("set_password", "clave-de-prueba-123")

    @factory.post_generation
    def _save(obj, create, extracted, **kwargs):
        if create:
            obj.save()
