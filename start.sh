#!/usr/bin/env bash
set -e

echo "Running migrations..."
uv run alembic upgrade head

echo "Starting bot..."
exec uv run python -m bot
