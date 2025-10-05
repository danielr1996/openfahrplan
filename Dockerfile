FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=2.2.0 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN pip install "poetry==${POETRY_VERSION}"
COPY pyproject.toml poetry.lock README.md ./
COPY src/ src/
COPY data/ data/
RUN pip install --upgrade pip build \
 && python -m build --wheel \
 && pip install --no-cache-dir dist/*.whl

EXPOSE 8050
CMD ["python", "-m", "openfahrplan"]
