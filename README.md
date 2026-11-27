# Preventa

Plataforma web para que una distribuidora mayorista reciba los pedidos de sus almacenes clientes de forma ordenada, en lugar de tomarlos por teléfono o WhatsApp.

> Nombre provisorio. Estado: **Sprint 0** (esqueleto del proyecto, sin reglas de negocio implementadas).

## Qué problema resuelve

La distribuidora recibe pedidos por varios canales, los transcribe a mano y arma el reparto con errores: productos sin stock, precios desactualizados, pedidos que llegan después del cierre y pedidos chicos que no conviene repartir.

Con Preventa, cada almacén entra a un catálogo con sus precios, arma el pedido y lo confirma antes del horario de corte de su zona. La distribuidora ve los pedidos del día, avanza sus estados y obtiene el consolidado para armar el reparto.

## Demo en producción

[PENDIENTE] URL del frontend (Vercel) y de la API (Render).

Usuarios de prueba por rol:

| Rol | Email | Contraseña |
|---|---|---|
| Administrador | [PENDIENTE] | [PENDIENTE] |
| Operador | [PENDIENTE] | [PENDIENTE] |
| Cliente | [PENDIENTE] | [PENDIENTE] |

## Capturas

[PENDIENTE]

## Arquitectura

Monorepo con una API REST en Django y un frontend React separado, cada uno desplegado por su lado.

```
preventa/
├── backend/    API REST (Django + DRF)  → Render
├── frontend/   SPA (React + Vite)       → Vercel
└── docs/       reglas de negocio, modelo de datos, API, deploy y ADRs
```

Capas del backend, en cada app de Django:

1. `views.py`: recibe la request, valida permisos y delega. Sin lógica de negocio.
2. `serializers.py`: valida formato y tipos de los datos de entrada y arma la salida.
3. `services.py`: aplica las reglas de negocio (RN-xx) dentro de transacciones.
4. `selectors.py`: consultas de lectura reutilizables.
5. `models.py`: estructura de datos, restricciones de base y métodos simples.

Las reglas viven en `services.py`; el frontend repite algunas validaciones solo para mejorar la experiencia. Ver [docs/decisiones/](docs/decisiones/).

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Python 3.12, Django 5, Django REST Framework |
| Autenticación | djangorestframework-simplejwt (access en memoria, refresh en cookie httpOnly) |
| Base de datos | PostgreSQL 16 (Docker en desarrollo; Supabase o Render en producción) |
| Documentación API | drf-spectacular (Swagger UI en `/api/docs/`) |
| Tests backend | pytest, pytest-django, factory-boy, coverage |
| Calidad backend | ruff (lint + formato) |
| Frontend | React 19, Vite, TypeScript, Tailwind CSS |
| Datos en el front | TanStack Query, axios, React Router |
| Formularios | React Hook Form + Zod |
| Tests frontend | Vitest + Testing Library |
| Calidad frontend | ESLint + Prettier |
| CI | GitHub Actions |
| Deploy | Render (API) y Vercel (frontend) |

## Requisitos previos

- Python 3.12
- Node.js 22 y npm
- Docker y Docker Compose
- Git

## Instalación local

```bash
# 1. Clonar
git clone <url-del-repo> preventa
cd preventa

# 2. Base de datos (PostgreSQL 16 en Docker)
docker compose up -d db
# Si el puerto 5432 está ocupado: POSTGRES_PORT=5433 docker compose up -d db
# (y usar ese puerto en DATABASE_URL de backend/.env)

# 3. Backend
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements/dev.txt
cp .env.example .env          # completar SECRET_KEY
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver    # http://localhost:8000

# 4. Frontend (en otra terminal)
cd frontend
npm install
cp .env.example .env.local
npm run dev                   # http://localhost:5173

# 5. Hooks de pre-commit (una vez, desde la raíz)
pre-commit install
```

## Variables de entorno

**backend/.env** (ver `backend/.env.example`)

| Variable | Descripción |
|---|---|
| `SECRET_KEY` | Clave secreta de Django |
| `DEBUG` | `True` solo en desarrollo |
| `ALLOWED_HOSTS` | Hosts permitidos, separados por coma |
| `DATABASE_URL` | Conexión a PostgreSQL |
| `CORS_ALLOWED_ORIGINS` | Orígenes del frontend, separados por coma |
| `CSRF_TRUSTED_ORIGINS` | Orígenes confiables para CSRF |
| `JWT_REFRESH_COOKIE_SECURE` | `False` solo en desarrollo local (http) |
| `DJANGO_SETTINGS_MODULE` | Opcional. `config.settings.dev` por defecto; `config.settings.prod` en Render |

**frontend/.env.local** (ver `frontend/.env.example`)

| Variable | Descripción |
|---|---|
| `VITE_API_URL` | URL base de la API, ej. `http://localhost:8000/api/v1` |

Nunca se suben archivos `.env` con claves reales.

## Tests y lint

```bash
# Backend (con la base levantada)
cd backend
pytest
coverage run -m pytest && coverage report
ruff check .
ruff format --check .

# Frontend
cd frontend
npm run lint
npm run format:check
npm run test
npm run build
```

El CI (GitHub Actions) corre lo mismo en cada PR a `main`.

## Documentación de la API

Swagger UI: <http://localhost:8000/api/docs/> (local) · [PENDIENTE] producción.

Cómo autenticarse: [docs/api.md](docs/api.md).

## Reglas de negocio

Ver [docs/reglas-de-negocio.md](docs/reglas-de-negocio.md) (RN-01 a RN-14) y [docs/modelo-datos.md](docs/modelo-datos.md).

## Flujo de trabajo con Git

- Todo cambio sale de un issue del tablero, se hace en su rama y entra a `main` por un PR con CI en verde.
- `main` está protegida: sin commits directos, solo merge de PR con checks aprobados (squash).
- Ramas: `feature/<nº-issue>-<descripcion-corta>` (ej. `feature/23-pedido-minimo`), `fix/...`, `docs/...`, `chore/...`, `test/...`.
- Commits con [Conventional Commits](https://www.conventionalcommits.org/es/), en español:

  ```
  feat(pedidos): validar pedido minimo por zona (RN-01)
  fix(catalogo): excluir productos sin precio en la lista
  ```

- PRs con el mismo formato de título, `Closes #<issue>` y el checklist de autorrevisión de la plantilla.
- Tablero en GitHub Projects: Backlog → Por hacer → En curso → En revisión → Hecho.

## Uso de IA

[PENDIENTE] Si la cátedra lo permite, declarar acá qué se hizo con asistencia de IA (documentación, revisión, scaffolding).

## Autor

[PENDIENTE]

---

Código propiedad de PB DevHouse. Sin licencia abierta.
