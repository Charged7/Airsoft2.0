FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./

RUN uv sync --locked --no-dev --no-install-project

COPY . .

ENV PATH="/app/.venv/bin:$PATH"

RUN chmod +x scripts/render-start.sh

CMD ["scripts/render-start.sh"]
