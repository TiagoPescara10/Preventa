# API

- Base: `/api/v1/`
- Documentación interactiva (Swagger UI): `/api/docs/` — local: <http://localhost:8000/api/docs/>
- Esquema OpenAPI: `/api/schema/`

## Autenticación

JWT con `djangorestframework-simplejwt`:

| Token | Duración | Dónde viaja |
|---|---|---|
| Access | 15 minutos | En el body de la respuesta; el frontend lo guarda **en memoria** y lo manda en `Authorization: Bearer <token>` |
| Refresh | 7 días | Solo en una cookie `httpOnly` (`refresh_token`, path `/api/v1/auth/`) |

| Método | Endpoint | Qué hace |
|---|---|---|
| POST | `/api/v1/auth/login/` | `{"email", "password"}` → `{"access", "usuario"}` + cookie de refresh |
| POST | `/api/v1/auth/refresh/` | Con la cookie → `{"access"}` nuevo |
| POST | `/api/v1/auth/logout/` | Invalida el refresh de la cookie (blacklist) y borra la cookie → `204` |
| GET | `/api/v1/auth/me/` | Usuario autenticado |
| GET | `/api/v1/health/` | Chequeo de vida, sin autenticación |

Las llamadas desde el frontend usan `withCredentials: true` para que el navegador mande la cookie.

Detalles:

- Login fallido (password incorrecta, email inexistente o usuario inactivo): `401` con el mismo mensaje genérico, para no revelar si el email existe.
- Refresh sin cookie, con un token inválido o expirado, o con uno invalidado por logout: `401`.
- Logout invalida el refresh en el servidor con la blacklist de simplejwt (`rest_framework_simplejwt.token_blacklist`), así que una copia del token deja de servir aunque no haya expirado. Si no hay cookie o el token ya es inválido, responde `204` igual.
- El access token no se invalida con el logout: sigue sirviendo hasta que expira (máximo 15 minutos). El frontend lo descarta de memoria.

## Errores

- Reglas de negocio: `400` (datos inválidos) o `409` (conflicto con el estado actual) con `{"codigo": "RN-xx", "detalle": "..."}`. Ver [reglas-de-negocio.md](reglas-de-negocio.md).
- Acción no permitida para el rol: `403`.
- Recurso de otro cliente: `404` (no se revela que existe).
