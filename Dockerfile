FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    OMEGA_HOME=/data/omega \
    OMEGA_WORKSPACE=/workspace

WORKDIR /app
COPY pyproject.toml README.md /app/
COPY omega /app/omega
COPY config /app/config
COPY examples /app/examples

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

WORKDIR /workspace
EXPOSE 8765
CMD ["omega", "serve", "--host", "0.0.0.0", "--port", "8765"]
