FROM python:3.13-bookworm AS builder
WORKDIR /app
RUN pip install --no-cache-dir poetry==2.3.2
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
COPY pyproject.toml ./
RUN poetry install --no-root --only main --no-interaction

FROM python:3.13-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends netcat-traditional && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/app
ENV PATH="/opt/app/.venv/bin:$PATH"
COPY --from=builder /app/.venv /opt/app/.venv
COPY lib /opt/app/lib
COPY bin /opt/app/bin
COPY entrypoint.sh /opt/app/entrypoint.sh
RUN chmod +x /opt/app/entrypoint.sh
ENTRYPOINT ["/opt/app/entrypoint.sh"]
