# Render deploy guide

This project is prepared for a free Render web service that exposes the Django REST API.

## Render Blueprint

Use the repository Blueprint:

```text
https://dashboard.render.com/blueprint/new?repo=https://github.com/Charged7/Airsoft2.0
```

Render will read `render.yaml` and create one Docker-based web service named `airsoft2-api`.

The Blueprint sets `SECURE_SSL_REDIRECT=True` and a short HSTS window for the demo service. If you attach a custom domain later, review those settings before increasing HSTS duration.

## Before Pushing to GitHub

The local repository currently tracks files that should not be deployed as source code:

```text
.env
db.sqlite3
staticfiles/
```

Before pushing the Render configuration, remove them from Git tracking while keeping local copies:

```sh
git rm --cached .env db.sqlite3
git rm --cached -r staticfiles
git add .dockerignore .gitignore render.yaml scripts/render-start.sh RENDER_DEPLOY.md config/settings.py Dockerfile
git commit -m "Prepare Django API for Render deployment"
git push origin main
```

If `.env` was already pushed to a public repository, rotate `SECRET_KEY`. Render generates a fresh production `SECRET_KEY` from `render.yaml`.

## What Render Runs

The Docker image starts with `scripts/render-start.sh`:

```sh
python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py seed_products
gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}"
```

This keeps the API usable on the free plan even when the local SQLite database is recreated.

## URLs for Frontend

After deploy, give the frontend developer:

```text
https://<your-render-service>.onrender.com/api/v1/health/
https://<your-render-service>.onrender.com/api/v1/products/
https://<your-render-service>.onrender.com/api/v1/quiz/questions/
https://<your-render-service>.onrender.com/api/v1/quiz/submit/
```

## Free Plan Caveat

Render Free can spin down after inactivity and its local filesystem is not durable. Product catalog data is reseeded on startup, but quiz submissions and any runtime SQLite writes can disappear after restart, redeploy, or spin-down.

For stable data, upgrade to a paid web service with a persistent disk or move the database to PostgreSQL.

## CORS

The free demo config sets:

```text
CORS_ALLOW_ALL_ORIGINS=True
CORS_ALLOW_CREDENTIALS=False
```

This is convenient for frontend testing from any local or hosted origin. Before production, replace it with a strict `CORS_ALLOWED_ORIGINS` value containing only the real frontend URL.
