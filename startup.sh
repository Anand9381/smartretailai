#!/usr/bin/env bash
set -euo pipefail

export PORT="${PORT:-8000}"
export WEB_CONCURRENCY="${WEB_CONCURRENCY:-1}"
export GUNICORN_THREADS="${GUNICORN_THREADS:-2}"
export GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-120}"

exec gunicorn \
  --bind "0.0.0.0:${PORT}" \
  --workers "${WEB_CONCURRENCY}" \
  --threads "${GUNICORN_THREADS}" \
  --timeout "${GUNICORN_TIMEOUT}" \
  --access-logfile - \
  --error-logfile - \
  app:app
