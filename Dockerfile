# GridPulse AI — Backend Dockerfile
# Uses python:3.11-slim (bookworm) with NO apt-get installs.
# asyncpg is a pure-Python Postgres driver — libpq-dev is not needed.
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies only — no system packages required
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src/ ./src/
COPY seeds/ ./seeds/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Ensure all package __init__.py files exist
RUN touch src/__init__.py src/app/__init__.py src/app/core/__init__.py \
    src/app/models/__init__.py src/app/schemas/__init__.py \
    src/app/services/__init__.py src/app/routes/__init__.py \
    src/app/database/__init__.py

EXPOSE 8000

CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
