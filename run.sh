#!/usr/bin/env bash
set -euo pipefail

# Lightweight launcher for development or simple deployments
VENV_DIR=${VENV_DIR:-venv}
if [ -f "$VENV_DIR/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
fi

GUNICORN_BIN="${GUNICORN_BIN:-$VENV_DIR/bin/gunicorn}"
if [ ! -x "$GUNICORN_BIN" ]; then
  # fallback to system gunicorn
  if command -v gunicorn >/dev/null 2>&1; then
    GUNICORN_BIN=$(command -v gunicorn)
  else
    echo "gunicorn not found. Please install requirements or set GUNICORN_BIN." >&2
    exit 1
  fi
fi

HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}
WORKERS=${GUNICORN_WORKERS:-3}

exec "$GUNICORN_BIN" -w "$WORKERS" -b "$HOST:$PORT" "app:create_app()"
