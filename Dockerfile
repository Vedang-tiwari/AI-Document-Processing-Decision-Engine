FROM python:3.12-slim

# Install system dependencies including Tesseract OCR and libmagic
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    tesseract-ocr-eng \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency definition
COPY pyproject.toml .env.example ./

# Install python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    pydantic \
    pydantic-settings \
    sqlalchemy \
    alembic \
    psycopg2-binary \
    aiosqlite \
    celery \
    redis \
    pymupdf \
    pytesseract \
    pillow \
    "pyjwt[crypto]" \
    bcrypt \
    python-multipart \
    pyyaml \
    httpx

# Copy project files
COPY backend /app/backend
COPY configs /app/configs
COPY data /app/data
COPY scripts /app/scripts
COPY alembic.ini /app/alembic.ini

# Create storage directory
RUN mkdir -p /app/storage

ENV PYTHONPATH=/app/backend:/app
EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
