# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

FROM base AS builder
WORKDIR /app
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential gcc \
 && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml README.md ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip build wheel
COPY src/ src/
COPY data/ data/
RUN --mount=type=cache,target=/root/.cache/pip \
    pip wheel --wheel-dir /wheels .

FROM base AS runner
ENV OPENFAHRPLAN_DATA_DIR=/app/data
WORKDIR /app
COPY --from=builder /wheels /wheels
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-index --find-links=/wheels /wheels/*.whl
COPY data/ data/
RUN for f in agency routes stop_times stops transfers trips; do \
      test -f "/app/data/parquet/vgn/$f.parquet" || { echo "Missing $f.parquet"; exit 1; }; \
    done
EXPOSE 8050
CMD ["python", "-m", "openfahrplan"]
