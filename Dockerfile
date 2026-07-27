FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project --no-dev

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app

RUN uv sync --locked --no-dev

EXPOSE 8000

CMD ["sh", "-c", "uv run alembic upgrade head && uv run fastapi run app/main.py --host 0.0.0.0 --port 8000"]
