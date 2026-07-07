#!/usr/bin/env sh
set -eu

python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py seed_products

exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}"
