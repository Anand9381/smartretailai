web: gunicorn --bind=0.0.0.0:${PORT:-8000} --workers=${WEB_CONCURRENCY:-1} --threads=${GUNICORN_THREADS:-2} --timeout=${GUNICORN_TIMEOUT:-120} --access-logfile - --error-logfile - app:app
