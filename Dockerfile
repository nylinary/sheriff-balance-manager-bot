FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY bot/ bot/
COPY alembic.ini .
COPY alembic/ alembic/

RUN uv sync --frozen --no-dev

CMD ["uv", "run", "python", "-m", "bot"]
