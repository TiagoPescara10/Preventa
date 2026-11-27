# Preventa — Especificación del proyecto

Nov 27, 2026 · @Tiago

## Contexto y alcance

Preventa (nombre provisorio) es una plataforma web para que una distribuidora mayorista reciba los pedidos de sus almacenes clientes de forma ordenada, en lugar de tomarlos por teléfono o WhatsApp.

**Problema.** La distribuidora recibe pedidos por varios canales, los transcribe a mano y arma el reparto con errores: productos sin stock, precios desactualizados, pedidos que llegan después del cierre y pedidos chicos que no conviene repartir.

**Solución.** Cada almacén entra a un catálogo con sus precios, arma el pedido y lo confirma antes del horario de corte de su zona. La distribuidora ve los pedidos del día, avanza sus estados y obtiene el consolidado para armar el reparto.

**Caso de negocio.** Genérico: una distribuidora de productos de almacén y limpieza del interior de Córdoba, con 3 zonas de reparto y unos 60 almacenes clientes. Se valida con distribuidoras reales en la etapa de venta.

**Dentro del MVP**

- Autenticación con JWT y tres roles: Administrador, Operador y Cliente.
- Gestión de zonas, clientes, categorías, productos y listas de precios (con baja lógica).
- Catálogo para el cliente con su lista de precios y el stock disponible.
- Pedidos: crear, modificar y cancelar antes del corte; estados con historial.
- Panel de la distribuidora: pedidos por zona y fecha de entrega, y consolidado para armar.

**Fuera del MVP** (posibles versiones futuras)

- Pagos online, cuenta corriente y facturación electrónica con ARCA.
- Ruteo del reparto en mapa y app del repartidor.
- Notificaciones por WhatsApp o correo.
- Multi-distribuidora (SaaS con varias empresas en la misma instalación).

## Stack y arquitectura

Monorepo con una API REST en Django y un frontend React separado, cada uno desplegado por su lado.

| Capa | Tecnología | Para qué |
| --- | --- | --- |
| Backend | Python 3.12, Django 5, Django REST Framework | API REST, reglas de negocio, ORM y migraciones |
| Autenticación | djangorestframework-simplejwt | Access token en memoria, refresh token en cookie httpOnly |
| Base de datos | PostgreSQL 16 | Desarrollo con Docker; producción en Supabase o Render |
| Documentación API | drf-spectacular | Swagger UI en `/api/docs/` |
| Tests backend | pytest, pytest-django, factory-boy, coverage | Unitarios de servicios e integración de endpoints |
| Calidad backend | ruff (lint + formato) | Se corre en CI y con pre-commit |
| Frontend | React 19, Vite, TypeScript, Tailwind CSS | SPA responsive |
| Datos en el front | TanStack Query, axios, React Router | Llamadas a la API, caché y rutas por rol |
| Formularios | React Hook Form + Zod | Validación del lado del cliente |
| Tests frontend | Vitest + Testing Library | Componentes y hooks críticos |
| Calidad frontend | ESLint + Prettier | Se corre en CI |
| CI | GitHub Actions | Lint y tests en cada PR; `main` protegida |
| Deploy | Render (API) y Vercel (frontend) | Variables de entorno en cada plataforma |

**Capas del backend.** Cada app de Django separa responsabilidades así:

1. `views.py`: recibe la request, valida permisos y delega. No tiene lógica de negocio.
2. `serializers.py`: valida formato y tipos de los datos de entrada y arma la salida.
3. `services.py`: aplica las reglas de negocio (RN-xx) dentro de transacciones. Es lo que más se testea.
4. `selectors.py`: consultas de lectura reutilizables (filtros por rol, por zona, por fecha).
5. `models.py`: estructura de datos, restricciones de base y métodos simples.

Las reglas viven en `services.py` y no en las vistas ni en el frontend. El frontend repite algunas validaciones solo para mejorar la experiencia; la fuente de verdad es el backend.

## Roles y permisos

Tres roles, uno por usuario. Los permisos se controlan en el backend en cada endpoint; el frontend solo oculta lo que el rol no puede usar.

- **Administrador**: el dueño o encargado de la distribuidora. Configura todo.
- **Operador**: empleado de depósito o administración. Gestiona los pedidos del día.
- **Cliente**: el almacén. Cada usuario Cliente está vinculado a un solo comercio.

| Acción | Administrador | Operador | Cliente |
| --- | --- | --- | --- |
| Gestionar usuarios y roles | Sí | No | No |
| ABM de zonas y horarios de corte | Sí | No | No |
| ABM de clientes (comercios) | Sí | Solo ver | Solo ver el suyo |
| ABM de categorías y productos | Sí | Solo ver | No |
| Actualizar stock | Sí | Sí | No |
| ABM de listas de precios y precios | Sí | No | No |
| Ver catálogo con precios | Sí (cualquier lista) | Sí (cualquier lista) | Solo su lista |
| Crear pedido | Sí, a nombre de un cliente | Sí, a nombre de un cliente | Sí, para su comercio |
| Modificar o cancelar pedido antes del corte | Sí | Sí | Solo los suyos |
| Cancelar pedido después del corte | Sí | No | No |
| Avanzar estado (preparación, despacho, entrega) | Sí | Sí | No |
| Ver pedidos | Todos | Todos | Solo los suyos |
| Ver consolidado de armado | Sí | Sí | No |

Un intento de acción no permitida responde `403 Forbidden`. Pedir un recurso de otro cliente responde `404 Not Found` para no revelar que existe.

## Entidades y modelo de datos

Diez tablas en cuatro apps de Django. Todas tienen `id`, `creado_en` y `actualizado_en`; las que admiten baja lógica tienen `activo` (booleano).

| Entidad | App | Campos principales | Relaciones y restricciones |
| --- | --- | --- | --- |
| Usuario | usuarios | email (único, se usa para el login), nombre, rol (ADMIN, OPERADOR, CLIENTE), activo | Extiende `AbstractUser`. Si rol es CLIENTE, tiene `cliente` obligatorio |
| Zona | clientes | nombre (único), días de reparto (lunes a sábado), hora de corte, monto mínimo de pedido, activo | Tiene muchos clientes |
| Cliente | clientes | razón social, nombre de fantasía, CUIT (único), dirección, localidad, teléfono, activo | FK a Zona y a ListaPrecios. Un cliente puede tener varios usuarios |
| Categoría | catalogo | nombre (único), activo | Tiene muchos productos |
| Producto | catalogo | código (único), nombre, presentación (ej. "Bulto x10"), stock disponible (entero ≥ 0), activo | FK a Categoría |
| ListaPrecios | catalogo | nombre (único, ej. "Minorista", "Mayorista"), activo | Una lista se asigna a muchos clientes |
| Precio | catalogo | precio (decimal, > 0) | FK a ListaPrecios y a Producto. Único por par (lista, producto) |
| Pedido | pedidos | número (único, ej. A-1042), fecha de entrega, estado, total, observaciones | FK a Cliente, a Zona (copia al confirmar) y a Usuario (quien lo creó) |
| ItemPedido | pedidos | cantidad (entero > 0), precio unitario (copiado al confirmar), subtotal | FK a Pedido y a Producto. Único por par (pedido, producto) |
| HistorialEstado | pedidos | estado anterior, estado nuevo, fecha y hora, motivo (opcional) | FK a Pedido y a Usuario |

**Decisiones de diseño**

- Montos en `DecimalField(max_digits=12, decimal_places=2)`, nunca `float`.
- Precio unitario y zona se copian en el pedido al confirmar, para que un cambio posterior no altere pedidos ya hechos (RN-05).
- Nada se borra físicamente si tiene pedidos asociados: se desactiva (RN-09).
- Índices en `Pedido(fecha_entrega, estado)`, `Pedido(cliente)` y `Cliente(zona)`, que son los filtros del panel.
- El diagrama entidad-relación va como imagen en `docs/modelo-datos.md`, generado desde los modelos.

## Estados del pedido

&#91;embedded content: estados del pedido · 6 estados, 6 transiciones\]

Un pedido nace CONFIRMADO y solo avanza hacia la derecha. Cancelado, Entregado y No entregado son finales. Cualquier otra transición devuelve 409 (RN-10), y cada cambio queda en el historial con usuario y fecha.

## Reglas de negocio

Cada regla tiene un código que se usa en issues, commits y nombres de tests (`test_rn01_...`). Se implementan en `services.py` y se responden con errores claros: `400` para datos inválidos y `409` para conflictos con el estado actual.

Supuestos comunes: la hora de referencia es la de Córdoba (`America/Argentina/Cordoba`) y los feriados quedan fuera del MVP.

### RN-01 · Pedido mínimo por zona

**Regla.** Un pedido solo se confirma si su total es mayor o igual al monto mínimo de la zona del cliente.

**Ejemplo.** Zona Norte tiene mínimo de $150.000. Un pedido de $149.999 se rechaza con el faltante; uno de $150.000 se acepta.

**Tests.** Total por debajo del mínimo devuelve 400 con el faltante · total igual al mínimo se confirma · al modificar un pedido y bajar del mínimo, la modificación se rechaza.

### RN-02 · Fecha de entrega y horario de corte

**Regla.** Cada zona tiene días de reparto y una hora de corte. El corte de un reparto es el día anterior a esa hora. Al confirmar, el pedido se asigna al próximo reparto cuyo corte no pasó. Un pedido tardío no se rechaza: pasa al reparto siguiente y se le avisa al cliente.

**Ejemplo.** Zona Norte reparte martes y viernes, corte 18:00. Un pedido del lunes 17:59 sale el martes. Uno del lunes 18:01 sale el viernes.

**Tests.** Un minuto antes del corte asigna el reparto más cercano · un minuto después asigna el siguiente · cruce de semana (pedido del sábado) · zona sin días de reparto no permite pedir.

### RN-03 · Modificación y cancelación por el cliente

**Regla.** El cliente puede modificar o cancelar su pedido solo si está en estado CONFIRMADO y no pasó el corte de su fecha de entrega. Después del corte, el pedido queda bloqueado para el cliente.

**Ejemplo.** Pedido para el martes de Zona Norte: se puede modificar hasta el lunes 17:59.

**Tests.** Modificar antes del corte funciona · después del corte devuelve 409 · un pedido EN\_PREPARACION no se puede modificar aunque falte para el corte.

### RN-04 · Un pedido activo por cliente y fecha

**Regla.** Un cliente tiene como máximo un pedido no cancelado por fecha de entrega. Si quiere agregar productos, modifica el existente.

**Ejemplo.** Almacén Doña Rosa ya tiene el A-1042 para el martes. Un segundo pedido para el martes devuelve 409 con el número A-1042.

**Tests.** Segundo pedido misma fecha devuelve 409 · si el primero está cancelado, se permite uno nuevo · otra fecha de entrega se permite.

### RN-05 · Precios según la lista del cliente

**Regla.** El cliente ve y paga los precios de su lista. Un producto sin precio en esa lista no aparece en su catálogo y no se puede pedir. El precio unitario se copia al ítem al confirmar; si el pedido se modifica, los ítems sin cambios conservan su precio y los nuevos o cambiados toman el vigente.

**Ejemplo.** La yerba cuesta $38.500 en la lista Minorista. Después del pedido sube a $41.000: el pedido ya confirmado sigue en $38.500.

**Tests.** El catálogo filtra productos sin precio en la lista · pedir uno sin precio devuelve 400 · un cambio de precio no altera pedidos confirmados.

### RN-06 · Stock disponible y reserva

**Regla.** No se puede pedir más cantidad que el stock disponible. Al confirmar, el stock se reserva (se descuenta). Al modificar se ajusta solo la diferencia. Al cancelar o marcar NO\_ENTREGADO, se devuelve. Todo ocurre en una transacción con bloqueo de filas (`select_for_update`) para que dos pedidos simultáneos no vendan la misma unidad.

**Ejemplo.** Hay 5 bultos de aceite. Un pedido de 3 deja 2; otro de 3 se rechaza indicando que quedan 2.

**Tests.** Pedir más que el stock devuelve 400 · confirmar descuenta · cancelar devuelve · modificar de 3 a 5 descuenta 2 · dos confirmaciones concurrentes no dejan stock negativo.

### RN-07 · Cantidades e ítems válidos

**Regla.** Cada ítem tiene cantidad entera entre 1 y 999 bultos. Un producto aparece una sola vez por pedido. Un pedido tiene al menos un ítem.

**Tests.** Cantidad 0, negativa, decimal o mayor a 999 devuelve 400 · producto repetido devuelve 400 · pedido sin ítems devuelve 400.

### RN-08 · Total calculado en el servidor

**Regla.** El total y los subtotales los calcula siempre el backend con los precios de la base. Cualquier precio o total enviado por el frontend se ignora.

**Tests.** Un request con un total adulterado guarda el total correcto · subtotal = cantidad × precio unitario · total = suma de subtotales.

### RN-09 · Baja lógica

**Regla.** Zonas, clientes, productos, listas y usuarios no se borran: se desactivan. Un producto inactivo desaparece del catálogo pero sigue en los pedidos que ya lo tienen. Un cliente inactivo no puede crear pedidos. No se puede desactivar una zona que tenga clientes activos.

**Tests.** El catálogo excluye inactivos · pedir un producto inactivo devuelve 400 · un cliente inactivo recibe 403 al crear pedido · desactivar una zona con clientes activos devuelve 409.

### RN-10 · Transiciones de estado e historial

**Regla.** El estado de un pedido solo cambia por las transiciones permitidas (ver diagrama). Solo Administrador y Operador avanzan estados. Cada cambio guarda una fila en HistorialEstado con usuario, fecha y estado anterior. Una transición no permitida devuelve 409.

**Tests.** Cada transición válida funciona y deja historial · ENTREGADO a CONFIRMADO devuelve 409 · un Cliente que intenta avanzar estado recibe 403.

### RN-11 · Cancelación después del corte

**Regla.** Pasado el corte, solo el Administrador puede cancelar, y solo si el pedido todavía no fue DESPACHADO. El motivo es obligatorio y queda en el historial.

**Tests.** Admin cancela EN\_PREPARACION con motivo · sin motivo devuelve 400 · un Operador recibe 403 · un pedido DESPACHADO devuelve 409.

### RN-12 · Visibilidad por rol

**Regla.** Un Cliente solo ve sus pedidos, su comercio y el catálogo de su lista. Pedir un recurso ajeno responde 404.

**Tests.** El listado de pedidos de un Cliente solo trae los suyos · GET de un pedido de otro cliente devuelve 404.

### RN-13 · Consolidado de armado

**Regla.** Para una zona y una fecha de entrega, el consolidado suma la cantidad de cada producto de los pedidos CONFIRMADO y EN\_PREPARACION. Los cancelados no cuentan.

**Ejemplo.** Dos pedidos del martes en Zona Norte con 2 y 4 bultos de yerba dan 6 bultos de yerba en el consolidado.

**Tests.** Suma correcta por producto · excluye cancelados y otras zonas o fechas · consolidado vacío devuelve lista vacía.

### RN-14 · Numeración de pedidos

**Regla.** Cada pedido recibe un número correlativo y único con prefijo (A-1001, A-1002…) generado en el backend dentro de la transacción.

**Tests.** Dos pedidos seguidos tienen números consecutivos · no hay duplicados con creaciones concurrentes.

## Estructura de carpetas

Un solo repositorio (`preventa`) con `backend/`, `frontend/` y `docs/`. Cada app de Django repite la misma forma interna, así cualquier regla se encuentra rápido.

```text
preventa/
├── .github/
│   ├── workflows/
│   │   ├── backend.yml          # ruff + pytest con Postgres de servicio
│   │   └── frontend.yml         # eslint + vitest + build
│   ├── ISSUE_TEMPLATE/
│   │   ├── historia-de-usuario.md
│   │   ├── tarea-tecnica.md
│   │   └── bug.md
│   └── pull_request_template.md
├── backend/
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── dev.py
│   │   │   ├── test.py
│   │   │   └── prod.py
│   │   ├── urls.py              # /api/v1/... y /api/docs/
│   │   └── wsgi.py
│   ├── core/                    # piezas compartidas
│   │   ├── models.py            # TimeStampedModel, SoftDeleteModel
│   │   ├── permissions.py       # IsAdmin, IsOperador, IsCliente
│   │   ├── exceptions.py        # ReglaDeNegocioError -> 400/409
│   │   └── pagination.py
│   ├── apps/
│   │   ├── usuarios/
│   │   ├── clientes/            # Zona, Cliente
│   │   ├── catalogo/            # Categoria, Producto, ListaPrecios, Precio
│   │   └── pedidos/             # Pedido, ItemPedido, HistorialEstado
│   │       ├── migrations/
│   │       ├── tests/
│   │       │   ├── factories.py
│   │       │   ├── test_services.py # reglas RN-xx
│   │       │   └── test_api.py      # endpoints y permisos
│   │       ├── admin.py
│   │       ├── models.py
│   │       ├── serializers.py
│   │       ├── services.py
│   │       ├── selectors.py
│   │       ├── permissions.py
│   │       ├── views.py
│   │       └── urls.py
│   ├── requirements/
│   │   ├── base.txt
│   │   └── dev.txt
│   ├── manage.py
│   ├── pyproject.toml           # config de ruff y pytest
│   └── .env.example
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── api/                 # cliente axios + funciones por recurso
│   │   ├── components/ui/       # botones, inputs, tablas, toasts
│   │   ├── features/
│   │   │   ├── auth/
│   │   │   ├── catalogo/
│   │   │   ├── pedidos/
│   │   │   ├── clientes/
│   │   │   └── panel/           # pedidos del día y consolidado
│   │   ├── hooks/
│   │   ├── lib/                 # formato de moneda, fechas, zod schemas
│   │   ├── routes/              # rutas protegidas por rol
│   │   ├── types/
│   │   └── main.tsx
│   ├── .env.example
│   ├── eslint.config.js
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── docs/
│   ├── reglas-de-negocio.md     # copia de la sección RN-xx
│   ├── modelo-datos.md          # DER + decisiones
│   ├── api.md                   # cómo autenticarse y link a Swagger
│   ├── deploy.md                # Render + Vercel paso a paso
│   └── decisiones/              # ADRs cortos: 0001-monorepo.md...
├── docker-compose.yml           # Postgres local
├── .editorconfig
├── .gitignore
├── .pre-commit-config.yaml
└── README.md
```

**Contenido del README.md**: qué es y qué problema resuelve, demo en producción con usuarios de prueba por rol, capturas, arquitectura, stack, requisitos previos, instalación local paso a paso, variables de entorno, cómo correr tests y lint, link a Swagger, link a las reglas de negocio, flujo de trabajo con Git y autor.

## Qué va al repo y qué no

Al repo va todo lo que otra persona necesita para levantar el proyecto desde cero; quedan afuera los secretos, lo que se genera solo y lo personal de tu máquina.

| Va al repo | No va al repo |
| --- | --- |
| Código fuente de `backend/` y `frontend/` | `.env` con claves reales (sí va `.env.example` con valores de ejemplo) |
| Migraciones de Django (`migrations/*.py`) | Entornos virtuales (`.venv/`, `venv/`) y `node_modules/` |
| `requirements/*.txt` y `package-lock.json` | Builds y archivos generados (`dist/`, `staticfiles/`, `__pycache__/`) |
| Tests, factories y fixtures de demo sin datos reales | Bases locales (`db.sqlite3`), dumps y backups con datos de clientes |
| Configuración de lint, CI, Docker y pre-commit | Reportes de coverage (`htmlcov/`, `.coverage`) y logs |
| `docs/`, README, plantillas de issues y PRs | Archivos subidos por usuarios (`media/`) |
| `.editorconfig` y `.vscode/extensions.json` (recomendaciones) | Configuración personal del editor y del sistema (`.vscode/settings.json`, `.idea/`, `.DS_Store`) |

```text
# Python
__pycache__/
*.py[cod]
.venv/
venv/
.pytest_cache/
.ruff_cache/
.coverage
htmlcov/

# Django
*.sqlite3
media/
staticfiles/
*.log

# Node
node_modules/
dist/
.vite/
coverage/

# Entorno y secretos
.env
.env.*
!.env.example

# Editor y sistema
.vscode/*
!.vscode/extensions.json
.idea/
.DS_Store
Thumbs.db

# Datos
*.dump
*.sql.gz
```

**Visibilidad.** Como después se vende, el repo va **privado** y se invita a los supervisores como colaboradores con permiso de lectura. Sin licencia abierta: el código es de PB DevHouse.

**Si se filtra un secreto**: rotarlo de inmediato (cambiar la clave en el servicio). Borrarlo del historial no alcanza, porque ya pudo haber sido copiado.

## Convenciones de Git y del tablero

Todo cambio sale de un issue del tablero, se hace en su rama y entra a `main` por un PR con CI en verde.

**Ramas**

- `main`: protegida. Sin commits directos; solo merge de PR con checks aprobados.
- `feature/<nº-issue>-<descripcion-corta>`: por ejemplo `feature/23-pedido-minimo`.
- `fix/<nº-issue>-<descripcion>`, `docs/...`, `chore/...` y `test/...` según el tipo.

**Commits** con Conventional Commits, en español, chicos y frecuentes:

```text
feat(pedidos): validar pedido minimo por zona (RN-01)
fix(catalogo): excluir productos sin precio en la lista
test(pedidos): cubrir corte horario un minuto antes y despues
docs(readme): agregar pasos de instalacion local
chore(ci): correr pytest con postgres en github actions
```

**Pull requests**: título con el mismo formato, descripción con qué cambia y cómo probarlo, `Closes #23` para cerrar el issue y un checklist de autorrevisión (tests, lint, sin secretos, docs actualizadas). Merge con **squash** para que `main` quede legible.

**Tablero en GitHub Projects**

- Columnas: Backlog → Por hacer → En curso → En revisión → Hecho.
- Campos: Sprint (iteración de 1 semana), Prioridad (Alta, Media, Baja), Estimación (1, 2, 3, 5, 8) y Área (Backend, Frontend, Infra, Docs).
- Etiquetas: `historia`, `tarea`, `bug`, `docs`, `test`, y una por regla cuando aplica (`RN-01`…).
- Cada historia de usuario es un issue con criterios de aceptación; sus tareas técnicas van como sub-issues.
- Automatizaciones del Project: issue nuevo a Backlog, PR abierto a En revisión, PR mergeado a Hecho.

**Uso de IA.** Si la cátedra lo permite, se declara en el README qué se hizo con asistencia de IA (documentación, revisión, scaffolding). Los commits los hace el autor desde su cuenta.

## Prompt para Claude Code (Sprint 0)

Este prompt arma solo el esqueleto del proyecto: carpetas, configuración, CI y plantillas. No implementa reglas de negocio y no hace commits, así el historial queda a tu nombre.

Antes de usarlo:

1. Creá el repo privado `preventa` en GitHub, clonalo y abrí Claude Code en esa carpeta.
2. Exportá este documento como Markdown y guardalo en `docs/especificacion.md`.
3. Pegá el prompt.

```text
Sos un desarrollador senior ayudando a armar el Sprint 0 de un proyecto integrador.
Lee primero docs/especificacion.md completo. Es la fuente de verdad: stack,
estructura de carpetas, .gitignore y convenciones.

TAREA: crear el esqueleto del monorepo exactamente con la estructura de la
seccion "Estructura de carpetas". Nada de logica de negocio todavia.

BACKEND (backend/)
- Django 5 + DRF, settings divididos en base/dev/test/prod, variables con
  django-environ leidas de .env.
- Modelo de usuario propio apps/usuarios.Usuario (AbstractUser, login por email,
  campo rol con choices ADMIN/OPERADOR/CLIENTE) configurado en AUTH_USER_MODEL
  ANTES de la primera migracion. El vinculo con Cliente queda para despues.
- core/: TimeStampedModel y SoftDeleteModel abstractos, permisos IsAdmin,
  IsOperador, IsCliente, una excepcion ReglaDeNegocioError y su handler que
  devuelve 400 o 409 con {"codigo": "RN-xx", "detalle": "..."}.
- Apps clientes, catalogo y pedidos creadas y registradas, con los archivos
  de la estructura (models, serializers, services, selectors, permissions,
  views, urls, tests/) vacios o con un docstring de que va en cada uno.
- simplejwt (access 15 min en el body, refresh 7 dias en cookie httpOnly),
  drf-spectacular en /api/docs/, django-cors-headers, rutas bajo /api/v1/.
- Endpoint GET /api/v1/health/ y un test con pytest que lo cubra.
- pyproject.toml con ruff y pytest-django; requirements/base.txt y dev.txt
  con versiones fijadas.

FRONTEND (frontend/)
- Vite + React + TypeScript + Tailwind, ESLint + Prettier, Vitest +
  Testing Library con un test de ejemplo.
- React Router con rutas placeholder: /login, /catalogo, /mis-pedidos,
  /panel, y un componente de ruta protegida por rol (sin logica real aun).
- src/api/client.ts con axios leyendo VITE_API_URL.

RAIZ
- docker-compose.yml con PostgreSQL 16 para desarrollo.
- .gitignore igual al de la especificacion, .editorconfig,
  .pre-commit-config.yaml (ruff, eslint, prettier, detect-private-key).
- .env.example en backend/ y frontend/ sin secretos reales.
- .github/workflows/backend.yml (ruff + pytest con servicio postgres) y
  frontend.yml (lint + test + build), disparados en pull_request a main.
- .github/ISSUE_TEMPLATE/ historia-de-usuario.md ("Como <rol> quiero <accion>
  para <beneficio>", criterios de aceptacion, reglas RN relacionadas),
  tarea-tecnica.md y bug.md; pull_request_template.md con descripcion,
  como probar, Closes #, y checklist de autorrevision.
- README.md con todas las secciones de la especificacion; lo que todavia no
  existe (demo, capturas) queda como [PENDIENTE].
- docs/decisiones/0001-monorepo.md y 0002-capa-de-servicios.md, cortos.

RESTRICCIONES
- NO hagas git commit, git push ni crees ramas. Yo hago los commits.
- No inventes reglas de negocio ni modelos fuera de Usuario y los abstractos.
- No pongas claves reales en ningun archivo.
- Codigo y comentarios en espanol para el dominio, ingles para lo tecnico.

AL TERMINAR
1. Verifica que corran: pytest, ruff check, npm run lint, npm run test,
   npm run build, y docker compose up -d db + migrate.
2. Dame la lista de comandos para levantar todo en local.
3. Proponeme como dividir lo creado en 6 a 10 commits chicos con mensajes
   Conventional Commits, en orden, indicando que archivos van en cada uno.
```

Después de correrlo, revisá cada archivo antes de commitear: lo que entra a tu historial lo tenés que poder explicar en la defensa.
