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
| POST | `/api/v1/auth/logout/` | Borra la cookie de refresh |
| GET | `/api/v1/auth/me/` | Usuario autenticado |
| GET | `/api/v1/health/` | Chequeo de vida, sin autenticación |

Las llamadas desde el frontend usan `withCredentials: true` para que el navegador mande la cookie.

## Errores

- Reglas de negocio: `400` (datos inválidos) o `409` (conflicto con el estado actual) con `{"codigo": "RN-xx", "detalle": "..."}`. Ver [reglas-de-negocio.md](reglas-de-negocio.md).
- Acción no permitida para el rol: `403`.
- Recurso de otro cliente: `404` (no se revela que existe).
