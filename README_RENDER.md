Quick deploy to Render

1. Ensure your repo contains:
   - `requirements.txt` (done)
   - `Procfile` (done)
   - `render.yaml` (optional, helps with Render web service config)
   - `manage.py`, `liontechweb/asgi.py`, `liontechweb/wsgi.py` (present)

2. Important environment variables on Render:
   - SECRET_KEY: a secure random string
   - DEBUG: False
   - ALLOWED_HOSTS: comma-separated hosts (example: 0.0.0.0,127.0.0.1,your-app.onrender.com)
   - DATABASE_URL: If using Postgres, set this (Render provides managed Postgres)

3. Static files
   - This settings assume WhiteNoise will serve static assets. Run `python manage.py collectstatic --noinput` as part of build, or configure static publish in Render.

4. Database
   - For production, use Postgres on Render. Add `psycopg2-binary` to requirements (done) and set `DATABASE_URL` env var.

5. Build & Start commands
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn liontechweb.asgi:application --bind 0.0.0.0:$PORT -k uvicorn.workers.UvicornWorker`

6. Optional
   - Add `runtime.txt` to pin Python version (e.g., `python-3.11.6`)

7. Troubleshooting
   - Check logs on Render for errors. If you see static file 404s, ensure `collectstatic` ran and `STATIC_ROOT` is set.
