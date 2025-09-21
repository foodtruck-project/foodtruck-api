FROM python:3.12-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_CACHE_DIR=/opt/uv-cache/

WORKDIR /app

COPY pyproject.toml .
COPY uv.lock .

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project


RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked


ADD . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

EXPOSE 8080

CMD ["uv", "run", "uvicorn", "projeto_aplicado.app:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers", "--workers", "4"]

CMD ["run", "uvicorn", "projeto_aplicado.app:app", "--host", "0.0.0.0", "--port", "8080"]

