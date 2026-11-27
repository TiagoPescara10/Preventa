# Deploy

[PENDIENTE] Completar con los pasos reales cuando se haga el primer deploy.

## API en Render

1. Crear un **Web Service** desde el repo, con root directory `backend`.
2. Build command: `pip install -r requirements/base.txt && python manage.py collectstatic --noinput && python manage.py migrate`
3. Start command: `gunicorn config.wsgi`
4. Variables de entorno:
   - `DJANGO_SETTINGS_MODULE=config.settings.prod`
   - `SECRET_KEY` (generada, nunca la de desarrollo)
   - `DATABASE_URL` (Postgres de Render o Supabase)
   - `ALLOWED_HOSTS` (dominio de Render)
   - `CORS_ALLOWED_ORIGINS` y `CSRF_TRUSTED_ORIGINS` (dominio de Vercel)
5. Health check path: `/api/v1/health/`

## Frontend en Vercel

1. Importar el repo, root directory `frontend`, framework Vite.
2. Variable de entorno: `VITE_API_URL=https://<api-en-render>/api/v1`
3. Agregar un rewrite de todas las rutas a `index.html` para que funcione React Router.
