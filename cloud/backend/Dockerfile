FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for psycopg
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (layer-cached: pyproject.toml changes infrequently)
COPY pyproject.toml .
# Create minimal app package so pip install . succeeds before full COPY
RUN mkdir -p app && touch app/__init__.py \
    && pip install --no-cache-dir . \
    && rm -rf app

# Copy application code (overwrites the stub)
COPY . .

# Run with single worker for in-memory rate limiter compatibility
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
